"""
Reads and writes sensitivity labels using powershell. It works on closed files.
Adapted from https://github.com/brunomsantiago/mip_python,
but modified to get custom properties directly from a sample office doc parsing XML (as powershell is
too slow reading them but acceptable writing) and to use openpyxl to read sensitivity labels unless otherwise
specified
Sample use:
    # If you know the sensitivity label to apply
    sl = SensitivityLabel("XXXXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX")
    sl.apply(my_filename)
    # If you don't know it, but what to clone an existing one (must be an Excel/Word/PowerPoint file)
    SensitivityLabel(reference_file).apply(my_file)
"""
import json
import os.path
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import pandas as pd
import openpyxl


def parse_xml_protection_properties(xml_string: str, fmtid: str = "{D5CDD505-2E9C-101B-9397-08002B2CF9AE}") -> dict:
    """Parses a xml_string with custom properties of an openXML doc and returns a dict"""
    root = ET.fromstring(xml_string)
    result = {}
    for child in root:
        if child.get('fmtid') != fmtid:
            continue
        key = child.attrib.get("name")
        value = child.findtext("{http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes}lpwstr")
        if key.startswith("MSIP_"):     # Only capture labels related to Microsoft Information Protection
            key = key.rsplit("_", maxsplit=1)[-1]
            result[key] = value
    return result


def read_label_regex(filepath, full_result=False, **kwargs) -> str | dict | None:
    """
    Reads information protection labels, by parsing openXML docs. Returns the label name if full_result=False (default),
    a dict with all information properties if full_result=True or None if no properties could be found
    """
    with ZipFile(filepath) as zipfile:
        name = "docProps/custom.xml"
        if name in zipfile.namelist():
            with zipfile.open(name) as f:
                content = f.read().decode()
                parsed = parse_xml_protection_properties(content)
                if parsed:
                    if full_result:
                        return parsed
                    else:
                        return parsed['Name']
        return None


def read_label_powershell(
        filepath,
        full_result=False,
        powershell=r'C:\WINDOWS\system32\WindowsPowerShell\v1.0\powershell.exe',
        stdout_encoding='iso8859-15',
):
    """
    Read sensitivity label from a Microsoft document
    This function uses a powershell command as subprocess to read the label_id
    of a microsoft document previously classified with the sensitivity label.
    This label_id can be used to apply the same sensitivity label to other
    documents.
    It relies on the 'Get-AIPFileStatus' powershell tool. To understand it
    better try running the command directly in powershell or look for the
    official Microsoft documentation.
    By default this function only returns the label_id, but if you want to see
    the full result from 'Get-AIPFileStatus' use full_result=True.
    """
    # The command to call in powershell. It includes the powershell tool
    # 'ConvertTo-Json' to make it easier to process the results in Python,
    # specially when the file path is too long, which may break lines.
    command = f"Get-AIPFileStatus -path '{filepath}' | ConvertTo-Json"
    # Executing it
    result = subprocess.Popen([powershell, command], stdout=subprocess.PIPE)
    result_lines = result.stdout.readlines()
    # Processing the results and saving to a dictionary
    clean_lines = [
        line.decode(stdout_encoding).rstrip('\r\n') for line in result_lines
    ]
    json_string = '\n'.join(clean_lines)
    result_dict = json.loads(json_string)
    # If selected, return the full results dictionary
    if full_result:
        return result_dict
    # If not returns only the label_id of interest to apply to other document
    # Per Microsoft documentation if a sensitivity label has both a
    # 'MainLabelId' and a 'SubLabelId', only the 'SubLabelId' should be used
    # with 'Set-AIPFileLabel' tool to set the label in a new document.
    label_id = (
        result_dict['SubLabelId']
        if result_dict['SubLabelId']
        else result_dict['MainLabelId']
    )
    return label_id


def apply_label(
        filepath,
        label_id,
        powershell=r'C:\WINDOWS\system32\WindowsPowerShell\v1.0\powershell.exe',
        stdout_encoding='iso8859-15',
):
    """
    Apply sensitivity label to a Microsoft document
    This function uses a powershell command as subprocess to apply it.
    It relies on the 'Set-AIPFileLabel' powershell tool. To understand it
    better try running the command directly in powershell or look for the
    official Microsoft documentation.
    Per Microsoft documentation if a sensitivity label has both a
    'MainLabelId' and a 'SubLabelId', only the 'SubLabelId' should be used
    with 'Set-AIPFileLabel' tool to set the label in a new document.
    The function returns the elapsed time to apply the label.
    """
    start = time.time()
    # The command to call in powershell
    command = f"(Set-AIPFileLabel -path '{filepath}' -LabelId '{label_id}').Status.ToString()"
    # Executing it
    result = subprocess.Popen([powershell, command], stdout=subprocess.PIPE)
    result_message = (
        result.stdout.readline().decode(stdout_encoding).rstrip('\r\n')
    )
    # If the command is not successful, raises an exception and display the
    #  message from 'Set-AIPFileLabel' tool
    if result_message != 'Success':
        raise Exception(result_message)
    end = time.time()
    return end - start


def is_guid(text: str) -> bool:
    """Checks if a text respond to pattern "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", which is an uuid version 4"""
    try:
        uuid.UUID(text, version=4)
        return True
    except:
        return False


class SensitivityLabel:
    """
    Class to add sensitivity labels to office files created programmatically
    Sample uses:
        # Apply a given label to a given file (faster)
        SensitivityLabel("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx").apply(my_file_path)
        # Copy label from an existing file to a given file
        SensitivityLabel(existing_file_full_path).apply(my_file_path)
    """

    powershell = r'C:\WINDOWS\system32\WindowsPowerShell\v1.0\powershell.exe'
    stdout_encoding = 'iso8859-15'

    def __init__(self, label_or_template: str, use_openpyxl: bool = True):
        """
        Creates a new SensitivityLabel instance, based on a guid or in an Excel/Word/PowerPoint file to use as a
        template

        """
        self.excel_custom_props = None
        self.use_openpyxl = use_openpyxl
        if is_guid(label_or_template):
            self.__label_id = label_or_template
        elif self.use_openpyxl and label_or_template.upper().endswith(".XLSX"):
            self.read_excel_custom_props(label_or_template)
        elif any(label_or_template.upper().endswith(ext) for ext in (".XLSX", ".DOCX", ".PPTX",
                                                                     ".PPTM", ".XLSXM", ".DOCM")):
            self.__label_id = read_label_regex(label_or_template)
            if not self.__label_id:
                # Not found. Falling back to the original powershell version, which is quite slow
                self.__label_id = read_label_powershell(label_or_template, powershell=self.powershell,
                                                        stdout_encoding=self.stdout_encoding)
        else:
            raise ValueError(f"Template file {label_or_template} not understood. Use a excel/word/powerpoint file")

    def read_excel_custom_props(self, file: str):
        """Reads custom props from an Excel file using openpyxl. Raises exception if file has no sensitivity
        label"""
        self.excel_custom_props = list()
        workbook_with_mip_label = openpyxl.load_workbook(file)
        # Copying custom properties from one workbook to another
        for prop in workbook_with_mip_label.custom_doc_props.props:
            if prop.name.startswith("MSIP"):
                if "SetDate" in prop.name:
                    # prop.value = pd.Timestamp.now().isoformat(timespec="seconds") + "Z"
                    prop.value = pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds")
                # print(f"{prop.name}: {prop.value}")
                self.excel_custom_props.append(prop)
        if not self.excel_custom_props:
            raise ValueError(f"The given file {file} contains no sensitivity label information")

    def apply_excel_custom_props(self, file: str):
        """Applies custom props to an Excel file using openpyxl"""
        if self.excel_custom_props:
            wb = openpyxl.load_workbook(file)
            for prop in self.excel_custom_props:
                wb.custom_doc_props.append(prop)
            wb.save(file)

    @property
    def label_id(self) -> str:
        return self.__label_id

    def apply(self, filename: str):
        """Applies current SensitivityLabel to a file. File must be closed to work properly"""
        if not os.path.isfile(filename):
            raise OSError(f"File not found: {filename}")
        # Use openpyxl if possible
        if self.use_openpyxl and self.excel_custom_props and filename.upper().endswith("XLSX"):
            self.apply_excel_custom_props(filename)
        else:
            apply_label(filename, self.label_id, powershell=self.powershell,
                        stdout_encoding=self.stdout_encoding)

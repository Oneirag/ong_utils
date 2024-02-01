"""
Function to validate user and password (of current logged in user) in windows, linux and macos
"""
from ong_utils.import_utils import raise_extra_exception
from ong_utils.utils import is_windows


def verify_credentials(username: str, domain: str, password: str, **kwargs) -> bool:
    """Checks if password is correct"""
    if not password:
        return False
    if is_windows():
        return _verify_credentials_windows(username, domain, password)
    else:
        return _verify_credentials_unix(username, password)


def _verify_credentials_windows(username: str, domain: str, password: str) -> bool:
    """Checks if password is correct in windows"""
    try:
        import win32security
        hUser = win32security.LogonUser(
            username,
            domain,
            password,
            # win32security.LOGON32_LOGON_NETWORK,
            win32security.LOGON32_LOGON_INTERACTIVE,
            win32security.LOGON32_PROVIDER_DEFAULT
        )
    except ModuleNotFoundError:
        raise_extra_exception("credentials")
    except win32security.error as e:
        return False
    except Exception as e:
        return False
    else:
        return True


def _verify_credentials_unix(username: str, password: str) -> bool:
    """Checks if password is correct in linux/macos"""
    try:
        import pam
        # Use PAM to authenticate the user
        pam_auth = pam.pam()
        return pam_auth.authenticate(username, password, service='login')
    except ModuleNotFoundError:
        raise_extra_exception("credentials")
    except pam.PAMError as e:
        print(f"Authentication failed: {e}")
        return False
    except Exception as e:
        print(e)
        return False


if __name__ == '__main__':
    from ong_utils.utils import get_current_user, get_current_domain
    import getpass

    password = getpass.getpass()

    print(verify_credentials(username=get_current_user(),
                             domain=get_current_domain(),
                             password=password))

    pass

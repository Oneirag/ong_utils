del *.whl
pip wheel . --no-deps
twine upload *.whl
del *.whl
rmdir /s /Q build
rmdir /s /Q src\ong_utils.egg-info

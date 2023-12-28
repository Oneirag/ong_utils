del *.whl
pip wheel . --no-deps
twine upload *.whl
del *.whl
rmdir /s build
rmdir /s src\ong_utils.egg-info

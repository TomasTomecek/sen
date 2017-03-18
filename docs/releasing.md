# How to release `sen`?

1. set correct version in `setup.py` and `sen/__init__.py`
2. verify that docker hub builds are passing
3. do **NOT** create feature branch with same name as tag
4. prepare changelog (`CHANGELOG.md` and release notes)
5. when tagged with release, verify that release was successful on travis
6. bump version in setup.py to `x.y.z-dev`


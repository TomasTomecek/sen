# How to release `sen`?

1. set correct version in `setup.py` and `sen/__init__.py`
2. verify that docker hub builds are passing: https://hub.docker.com/repository/docker/tomastomecek/sen/general
3. do **NOT** create feature branch with same name as tag
4. prepare changelog (`CHANGELOG.md` and release notes)
6. correct Docker Hub tags - let latest release point to `latest`
7. bump version in setup.py to `x.y.z-dev`


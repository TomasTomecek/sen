Run tests locally:

    $ tmt -v run -a provision -h local

Run tests in a container using podman:

    $ sudo dnf install tmt-provision-container
    $ tmt -v run -a provision -h container

For more info see:

- https://packit.dev/docs/testing-farm/
- [tmt @ DevConf 2021 slides](https://static.sched.com/hosted_files/devconfcz2021/37/tmt-slides.pdf)
- [fmf docs](https://fmf.readthedocs.io)
- [tmt docs](https://tmt.readthedocs.io)

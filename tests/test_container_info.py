from sen.docker_backend import DockerBackend, DockerContainer
from sen.tui.views.container_info import ProcessList
from tests.real import mock


def test_short_id():
    mock()
    b = DockerBackend()
    operation = DockerContainer({"Status": "Up", "Id": "voodoo"}, b).top()
    top_response = operation.response
    pt = ProcessList(top_response)

    # 24502
    #  \ 24542
    #     \ 23743
    #        \ 18725
    #        \ 18733
    #        \ 18743
    #        \ 23819

    root_process = pt.get_root_process()
    assert root_process.pid == "24502"
    assert pt.get_parent_process(root_process) is None

    p_24542 = pt.get_first_child_process(root_process)
    assert p_24542.pid == "24542"
    assert pt.get_last_child_process(root_process).pid == "24542"

    p_23743 = pt.get_first_child_process(p_24542)
    assert p_23743.pid == "23743"
    assert pt.get_last_child_process(p_24542).pid == "23743"

    p_18725 = pt.get_first_child_process(p_23743)
    assert p_18725.pid == "18725"
    assert pt.get_prev_sibling(p_18725) is None
    assert pt.get_parent_process(p_18725).pid == "23743"

    p_18733 = pt.get_next_sibling(p_18725)
    assert p_18733.pid == "18733"

    p_23819 = pt.get_last_child_process(p_23743)
    assert p_23819.pid == "23819"
    assert pt.get_next_sibling(p_23819) is None
    assert pt.get_parent_process(p_23819).pid == "23743"

    p_18743 = pt.get_prev_sibling(p_23819)
    assert p_18743.pid == "18743"

    assert pt.get_prev_sibling(p_18733) is p_18725
    assert pt.get_next_sibling(p_18733) is p_18743

    assert pt.get_prev_sibling(p_18743) is p_18733
    assert pt.get_next_sibling(p_18743) is p_23819

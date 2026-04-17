from school_mcp.errors import SchoolMcpError, AuthError, BusinessError, HttpError


def test_all_errors_inherit_from_base():
    assert issubclass(AuthError, SchoolMcpError)
    assert issubclass(BusinessError, SchoolMcpError)
    assert issubclass(HttpError, SchoolMcpError)


def test_error_carries_message():
    err = BusinessError("学号已存在")
    assert str(err) == "学号已存在"

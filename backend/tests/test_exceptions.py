from core.exceptions import (
    AppError, NotFoundError, ForbiddenError,
    FileTooLargeError, UnsupportedFileTypeError, SlotLimitError
)


def test_not_found_status():
    assert NotFoundError().status_code == 404


def test_forbidden_status():
    assert ForbiddenError().status_code == 403


def test_file_too_large_status_and_message():
    err = FileTooLargeError(50)
    assert err.status_code == 413
    assert "50" in err.detail


def test_unsupported_file_type_message():
    err = UnsupportedFileTypeError("virus.exe")
    assert err.status_code == 415
    assert "PDF" in err.detail
    assert "virus.exe" not in err.detail


def test_slot_limit_error():
    err = SlotLimitError(2)
    assert err.status_code == 400
    assert "2" in err.detail


def test_slot_limit_zero():
    err = SlotLimitError(0)
    assert "0" in err.detail


def test_app_error_inherits_correctly():
    err = AppError(418, "sou um bule")
    assert err.status_code == 418
    assert err.detail == "sou um bule"

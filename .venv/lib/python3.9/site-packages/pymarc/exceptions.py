# This file is part of pymarc. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution and at
# https://opensource.org/licenses/BSD-2-Clause. pymarc may be copied, modified,
# propagated, or distributed according to the terms contained in the LICENSE
# file.

"""Exceptions for pymarc."""


class PymarcException(Exception):
    """Base pymarc Exception."""

    pass


class FatalReaderError(PymarcException):
    """Error preventing further reading."""

    pass


class RecordLengthInvalid(FatalReaderError):
    """Invalid record length."""

    def __str__(self):
        return "Invalid record length in first 5 bytes of record"


class TruncatedRecord(FatalReaderError):
    """Truncated record data."""

    def __str__(self):
        return "Record length in leader is greater than the length of data"


class EndOfRecordNotFound(FatalReaderError):
    """Unable to locate end of record marker."""

    def __str__(self):
        return "Unable to locate end of record marker"


class RecordLeaderInvalid(PymarcException):
    """Unable to extract record leader."""

    def __str__(self):
        return "Unable to extract record leader"


class RecordDirectoryInvalid(PymarcException):
    """Invalid directory."""

    def __str__(self):
        return "Invalid directory"


class NoFieldsFound(PymarcException):
    """Unable to locate fields in record data."""

    def __str__(self):
        return "Unable to locate fields in record data"


class BaseAddressInvalid(PymarcException):
    """Base address exceeds size of record."""

    def __str__(self):
        return "Base address exceeds size of record"


class BaseAddressNotFound(PymarcException):
    """Unable to locate base address of record."""

    def __str__(self):
        return "Unable to locate base address of record"


class WriteNeedsRecord(PymarcException):
    """Write requires a pymarc.Record object as an argument."""

    def __str__(self):
        return "Write requires a pymarc.Record object as an argument"


class NoActiveFile(PymarcException):
    """There is no active file to write to in call to write."""

    def __str__(self):
        return "There is no active file to write to in call to write"


class FieldNotFound(PymarcException):
    """Record does not contain the specified field."""

    def __str__(self):
        return "Record does not contain the specified field"


class BadSubfieldCodeWarning(Warning):
    """Warning about a non-ASCII subfield code."""

    pass


class BadLeaderValue(PymarcException):
    """Error when setting a leader value."""

    pass


class MissingLinkedFields(PymarcException):
    """Error when a non-880 field has a subfield 6 that cannot be matched to an 880."""

    def __init__(self, field):
        """Initialize MissingLinkedFields with the `field` that lacks one or more target 880s."""
        super().__init__(field)
        self.field = field

    def __str__(self):
        return (
            self.field.tag
            + " field includes a subfield 6 but no linked fields could be found."
        )


# This alias for FatalReaderError is here to correct a misspelling that was
# introduced in v4.0.0. It can be removed in v5.0.0.

FatalReaderEror = FatalReaderError

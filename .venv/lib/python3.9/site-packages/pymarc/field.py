# This file is part of pymarc. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution and at
# https://opensource.org/licenses/BSD-2-Clause. pymarc may be copied, modified,
# propagated, or distributed according to the terms contained in the LICENSE
# file.

"""The pymarc.field file."""

import logging
from collections import defaultdict
from typing import List, Optional, Tuple, DefaultDict

from pymarc.constants import SUBFIELD_INDICATOR, END_OF_FIELD
from pymarc.marc8 import marc8_to_unicode


class Field:
    """Field() pass in the field tag, indicators and subfields for the tag.

    .. code-block:: python

        field = Field(
            tag = '245',
            indicators = ['0','1'],
            subfields = [
                'a', 'The pragmatic programmer : ',
                'b', 'from journeyman to master /',
                'c', 'Andrew Hunt, David Thomas.',
            ])

    If you want to create a control field, don't pass in the indicators
    and use a data parameter rather than a subfields parameter:

    .. code-block:: python

        field = Field(tag='001', data='fol05731351')
    """

    def __init__(
        self,
        tag: str,
        indicators: Optional[List[str]] = None,
        subfields: Optional[List[str]] = None,
        data="",
    ):
        """Initialize a field `tag`."""
        # attempt to normalize integer tags if necessary
        try:
            self.tag = "%03i" % int(tag)
        except ValueError:
            self.tag = "%03s" % tag

        # assume controlfields are numeric only; replicates ruby-marc behavior
        if self.tag < "010" and self.tag.isdigit():
            self.data = data
        else:
            self.indicators = [str(x) for x in (indicators or [])]
            self.subfields = subfields or []

    def __iter__(self):
        self.__pos = 0
        return self

    def __str__(self) -> str:
        """String representation of the field.

        A Field object in a string context will return the tag, indicators
        and subfield as a string. This follows MARCMaker format; see [1]
        and [2] for further reference. Special character mnemonic strings
        have yet to be implemented (see [3]), so be forewarned. Note also
        for complete MARCMaker compatibility, you will need to change your
        newlines to DOS format ('CRLF').

        [1] http://www.loc.gov/marc/makrbrkr.html#mechanics
        [2] http://search.cpan.org/~eijabb/MARC-File-MARCMaker/
        [3] http://www.loc.gov/marc/mnemonics.html
        """
        if self.is_control_field():
            text = "=%s  %s" % (self.tag, self.data.replace(" ", "\\"))
        else:
            text = "=%s  " % (self.tag)
            for indicator in self.indicators:
                if indicator in (" ", "\\"):
                    text += "\\"
                else:
                    text += "%s" % indicator
            for subfield in self:
                text += "$%s%s" % subfield
        return text

    def __getitem__(self, subfield) -> Optional[str]:
        """Retrieve the first subfield with a given subfield code in a field.

        .. code-block:: python

            field['a']

        Handy for quick lookups.
        """
        subfields = self.get_subfields(subfield)
        return subfields[0] if subfields else None

    def __contains__(self, subfield: Optional[str]) -> bool:
        """Allows a shorthand test of field membership.

        .. code-block:: python

            'a' in field

        """
        return bool(self.get_subfields(subfield))

    def __setitem__(self, code: str, value: str) -> None:
        """Set the values of the subfield code in a field.

        .. code-block:: python

            field['a'] = 'value'

        Raises KeyError if there is more than one subfield code.
        """
        subfields = self.get_subfields(code)
        if len(subfields) > 1:
            raise KeyError("more than one code '%s'" % code)
        elif len(subfields) == 0:
            raise KeyError("no code '%s'" % code)
        num_code = len(self.subfields) // 2
        while num_code >= 0:
            if self.subfields[(num_code * 2) - 2] == code:
                self.subfields[(num_code * 2) - 1] = value
                break
            num_code -= 1

    def __next__(self) -> Tuple[str, str]:
        if not hasattr(self, "subfields"):
            raise StopIteration
        while self.__pos < len(self.subfields):
            subfield = (self.subfields[self.__pos], self.subfields[self.__pos + 1])
            self.__pos += 2
            return subfield
        raise StopIteration

    def value(self) -> str:
        """Returns the field as a string w/ tag, indicators, and subfield indicators."""
        if self.is_control_field():
            return self.data
        return " ".join(subfield[1].strip() for subfield in self)

    def get_subfields(self, *codes) -> List[str]:
        """Get subfields matching `codes`.

        get_subfields() accepts one or more subfield codes and returns
        a list of subfield values.  The order of the subfield values
        in the list will be the order that they appear in the field.

        .. code-block:: python

            print(field.get_subfields('a'))
            print(field.get_subfields('a', 'b', 'z'))
        """
        return [subfield[1] for subfield in self if subfield[0] in codes]

    def add_subfield(self, code: str, value: str, pos=None) -> None:
        """Adds a subfield code/value to the end of a field or at a position (pos).

        .. code-block:: python

            field.add_subfield('u', 'http://www.loc.gov')
            field.add_subfield('u', 'http://www.loc.gov', 0)

        If pos is not supplied or out of range, the subfield will be added at the end.
        """
        append = pos is None or (pos + 1) * 2 > len(self.subfields)

        if append:
            self.subfields.append(code)
            self.subfields.append(value)
        else:
            i = pos * 2
            self.subfields.insert(i, code)
            self.subfields.insert(i + 1, value)

    def delete_subfield(self, code: str) -> Optional[str]:
        """Deletes the first subfield with the specified 'code' and returns its value.

        .. code-block:: python

            value = field.delete_subfield('a')

        If no subfield is found with the specified code None is returned.
        """
        try:
            codes = self.subfields[0::2]
            index = codes.index(code) * 2
            value = self.subfields.pop(index + 1)
            self.subfields.pop(index)
            return value
        except ValueError:
            return None

    def subfields_as_dict(self) -> DefaultDict[str, list]:
        """Returns the subfields as a dictionary.

        The dictionary is a mapping of subfield codes and values. Since
        subfield codes can repeat the values are a list.
        """
        keys = self.subfields[0::2]
        vals = self.subfields[1::2]
        subs: DefaultDict[str, list] = defaultdict(list)
        for k, v in zip(keys, vals):
            subs[k].append(v)
        return subs

    def is_control_field(self) -> bool:
        """Returns true or false if the field is considered a control field.

        Control fields lack indicators and subfields.
        """
        return self.tag < "010" and self.tag.isdigit()

    def linkage_occurrence_num(self) -> Optional[str]:
        """Return the 'occurrence number' part of subfield 6, or None if not present."""
        ocn = self["6"] or ""
        return ocn.split("-")[1].split("/")[0] if ocn else None

    def as_marc(self, encoding: str) -> bytes:
        """Used during conversion of a field to raw marc."""
        if self.is_control_field():
            return (self.data + END_OF_FIELD).encode(encoding)
        marc = self.indicator1 + self.indicator2
        for subfield in self:
            marc += SUBFIELD_INDICATOR + subfield[0] + subfield[1]

        return (marc + END_OF_FIELD).encode(encoding)

    # alias for backwards compatibility
    as_marc21 = as_marc

    def format_field(self) -> str:
        """Returns the field as a string w/ tag, indicators, and subfield indicators.

        Like :func:`Field.value() <pymarc.field.Field.value>`, but prettier
        (adds spaces, formats subject headings).
        """
        if self.is_control_field():
            return self.data
        fielddata = ""
        for subfield in self:
            if subfield[0] == "6":
                continue
            if not self.is_subject_field():
                fielddata += " %s" % subfield[1]
            else:
                if subfield[0] not in ("v", "x", "y", "z"):
                    fielddata += " %s" % subfield[1]
                else:
                    fielddata += " -- %s" % subfield[1]
        return fielddata.strip()

    def is_subject_field(self) -> bool:
        """Returns True or False if the field is considered a subject field.

        Used by :func:`format_field() <pymarc.field.Field.format_field>` .
        """
        return self.tag.startswith("6")

    @property
    def indicator1(self) -> str:
        """Indicator 1."""
        return self.indicators[0]

    @indicator1.setter
    def indicator1(self, value: str) -> None:
        """Indicator 1 (setter)."""
        self.indicators[0] = value

    @property
    def indicator2(self) -> str:
        """Indicator 2."""
        return self.indicators[1]

    @indicator2.setter
    def indicator2(self, value: str) -> None:
        """Indicator 2 (setter)."""
        self.indicators[1] = value


class RawField(Field):
    """MARC field that keeps data in raw, undecoded byte strings.

    Should only be used when input records are wrongly encoded.
    """

    def as_marc(self, encoding: Optional[str] = None):
        """Used during conversion of a field to raw marc."""
        if encoding is not None:
            logging.warning("Attempt to force a RawField into encoding %s", encoding)
        if self.is_control_field():
            return self.data + END_OF_FIELD.encode("ascii")
        marc = self.indicator1.encode("ascii") + self.indicator2.encode("ascii")
        for subfield in self:
            marc += (
                SUBFIELD_INDICATOR.encode("ascii")
                + subfield[0].encode("ascii")
                + subfield[1]
            )
        return marc + END_OF_FIELD.encode("ascii")


def map_marc8_field(f: Field) -> Field:
    """Map MARC8 field."""
    if f.is_control_field():
        f.data = marc8_to_unicode(f.data)
    else:
        f.subfields = [marc8_to_unicode(subfield) for subfield in f.subfields]
    return f

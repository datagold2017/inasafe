# coding=utf-8
"""Rounding and number formatting."""


from math import ceil

from safe.definitions.units import unit_mapping
from safe.utilities.i18n import locale

__copyright__ = "Copyright 2016, The InaSAFE Project"
__license__ = "GPL version 3"
__email__ = "info@inasafe.org"
__revision__ = '$Format:%H$'


def format_number(
        x, enable_rounding=True, is_population=True, coefficient=1):
    """Format a number according to the standards.

    :param x: A number to be formatted in a locale friendly way.
    :type x: int

    :param enable_rounding: Flag to enable a rounding.
    :type enable_rounding: bool

    :param is_population: Flag if the number is population. It needs to be
        used with enable_rounding.
    :type is_population: bool

    :param coefficient: Divide the result after the rounding.
    :type coefficient:float

    :returns: A locale friendly formatted string e.g. 1,000,0000.00
        representing the original x. If a ValueError exception occurs,
        x is simply returned.
    :rtype: basestring
    """
    if enable_rounding:
        x = rounding(x, is_population)

    x /= coefficient

    number = add_separators(x)
    return number


def add_separators(x):
    """Format integer with separator between thousands.

    :param x: A number to be formatted in a locale friendly way.
    :type x: int

    :returns: A locale friendly formatted string e.g. 1,000,0000.00
        representing the original x. If a ValueError exception occurs,
        x is simply returned.
    :rtype: basestring

    From http://
    stackoverflow.com/questions/5513615/add-thousands-separators-to-a-number

    Instead use this:
    http://docs.python.org/library/string.html#formatspec
    """
    try:
        s = '{0:,}'.format(x)
        # s = '{0:n}'.format(x)  # n means locale aware (read up on this)
    # see issue #526
    except ValueError:
        return x

    # Quick solution for the moment
    if locale() in ['id', 'fr']:
        # Replace commas with the correct thousand separator.
        s = s.replace(',', thousand_separator())
    return s


def decimal_separator():
    """Return decimal separator according to the locale.

    :return: The decimal separator.
    :rtype: basestring
    """
    lang = locale()

    if lang in ['id', 'fr']:
        return ','

    else:
        return '.'


def thousand_separator():
    """Return thousand separator according to the locale.

    :return: The thousand separator.
    :rtype: basestring
    """
    lang = locale()

    if lang in ['id']:
        return '.'

    elif lang in ['fr']:
        return ' '

    else:
        return ','


def round_affected_number(
        number,
        enable_rounding=False,
        use_population_rounding=False):
    """Tries to convert and round the number.

    Rounded using population rounding rule.

    :param number: number represented as string or float
    :type number: str, float

    :param enable_rounding: flag to enable rounding
    :type enable_rounding: bool

    :param use_population_rounding: flag to enable population rounding scheme
    :type use_population_rounding: bool

    :return: rounded number
    """
    decimal_number = float(number)
    rounded_number = int(ceil(decimal_number))
    if enable_rounding and use_population_rounding:
        # if uses population rounding
        return rounding(rounded_number, use_population_rounding)
    elif enable_rounding:
        return rounded_number

    return decimal_number


def rounding_full(number, is_population=False):
    """This function performs a rigorous rounding.

    :param number: The amount to round.
    :type number: int, float

    :param is_population: If we should use the population rounding rule, #4062.
    :type is_population: bool

    :returns: result and rounding bracket.
    :rtype: (int, int)
    """
    if number < 1000 and not is_population:
        rounding_number = 1  # See ticket #4062
    elif number < 1000 and is_population:
        rounding_number = 10
    elif number < 100000:
        rounding_number = 100
    else:
        rounding_number = 1000
    number = int(rounding_number * ceil(1.0 * number / rounding_number))
    return number, rounding_number


def rounding(number, is_population=False):
    """A shorthand for rounding_full(number)[0].

    :param number: The amount to round.
    :type number: int, float

    :param is_population: If we should use the population rounding rule, #4062.
    :type is_population: bool

    :returns: result and rounding bracket.
    :rtype: int
    """
    return rounding_full(number, is_population)[0]


def convert_unit(number, input_unit, expected_unit):
    """A helper to convert the unit.

    :param number: The number to update.
    :type number: int

    :param input_unit: The unit of the number.
    :type input_unit: safe.definitions.units

    :param expected_unit: The expected output unit.
    :type expected_unit: safe.definitions.units

    :return: The new number in the expected unit.
    :rtype: int
    """
    for mapping in unit_mapping:
        if input_unit == mapping[0] and expected_unit == mapping[1]:
            return number * mapping[2]
        if input_unit == mapping[1] and expected_unit == mapping[0]:
            return number / mapping[2]

    return None


def coefficient_between_units(unit_a, unit_b):
    """A helper to get the coefficient between two units.

    :param unit_a: The first unit.
    :type unit_a: safe.definitions.units

    :param unit_b: The second unit.
    :type unit_b: safe.definitions.units

    :return: The coefficient between these two units.
    :rtype: float
    """
    for mapping in unit_mapping:
        if unit_a == mapping[0] and unit_b == mapping[1]:
            return mapping[2]
        if unit_a == mapping[1] and unit_b == mapping[0]:
            return 1 / mapping[2]

    return None


def fatalities_range(number):
    """A helper to return fatalities as a range of number.

    See https://github.com/inasafe/inasafe/issues/3666#issuecomment-283565297

    :param number: The exact number. Will be converted as a range.
    :type number: int, float

    :return: The range of the number.
    :rtype: str
    """
    range_format = '{min_range} - {max_range}'
    more_than_format = '> {min_range}'
    ranges = [
        [0, 100],
        [100, 1000],
        [1000, 10000],
        [10000, 100000],
        [100000, float('inf')]
    ]
    for r in ranges:
        min_range = r[0]
        max_range = r[1]

        if max_range == float('inf'):
            return more_than_format.format(
                min_range=add_separators(min_range))
        elif min_range <= number <= max_range:
            return range_format.format(
                min_range=add_separators(min_range),
                max_range=add_separators(max_range))

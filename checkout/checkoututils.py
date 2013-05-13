from decimal import Decimal

class SalesTax(object):

    def __init__(self, rate, description):
        """
        Tax rate is in units of percent (%).
        """
        self.rate = rate
        self.description = description


class GST(SalesTax):

    def __init__(self):
        super(GST, self).__init__(Decimal('5'), 'GST')


class PST(SalesTax):

    def __init__(self, rate):
        super(PST, self).__init__(rate, 'PST')


class HST(SalesTax):

    def __init__(self, rate):
        super(HST, self).__init__(rate, 'HST')


class QST(SalesTax):

    def __init__(self, rate):
        super(QST, self).__init__(rate, 'QST')


def sales_taxes(province):
    """
    Returns an array of sales tax applicable for the given province.
    The province argument is expected to be the two letter provincial abbreviation.
    """
    province = province.upper()
    taxes = [GST()]

    if province == "AB":
        pass
    elif province == "BC":
        taxes.append(PST(Decimal('7')))
    elif province == "MB":
        taxes.append(PST(Decimal('7')))
    elif province == "NB":
        taxes = [HST(Decimal('13'))]
    elif province == "NL":
        taxes = [HST(Decimal('13'))]
    elif province == "NT":
        pass
    elif province == "NS":
        taxes = [HST(Decimal('15'))]
    elif province == "NU":
        # Nunavut
        pass
    elif province == "ON":
        taxes = [HST(Decimal('13'))]
    elif province == "PE":
        taxes = [HST(Decimal('14'))]
    elif province == "QC":
        taxes.append(QST(Decimal('9.975')))
    elif province == "SK":
        taxes.append(PST(Decimal('5')))
    elif province == "YT":
        # yukon
        pass
    else:
        raise Exception("Unrecognized province: " + str(province))
    return taxes

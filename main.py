import numpy as np

import esfa
from xcri import Xcri
from lxml import etree
import os
import pandas as pd


def main():
    provider_ukprn = 10000533
    # Get some open data
    courses = esfa.create_open_data(provider_ukprn=provider_ukprn, output_path='output' + os.sep + 'courses.csv')
    courses = pd.DataFrame(courses).replace({np.nan: None})
    # Merge the minimum collection
    data = pd.read_excel('examples' + os.sep + 'LSIP Minimal Data Collection Template Example.xlsx', sheet_name='Courses and qualifications', header=1)
    data = data.dropna(axis=0, how='all')
    data = data.dropna(axis=1, how='all')
    data = pd.merge(left=courses, right=data, left_on='Qualification.identifier', right_on='Qualification Aim Reference')
    data.drop(columns='Qualification Aim Reference', inplace=True)
    # Set some constants
    data['Presentation.start'] = '2022/23'
    data['Provider.name'] = 'Poppleton College'
    data['Presentation.costCurrency'] = 'GBP'
    xcri = Xcri(courses=data.to_dict('records'))
    xml = etree.tostring(xcri.to_xml(), pretty_print=True, encoding='utf-8')
    with open('output' + os.sep + 'example.xml', mode='wb') as file:
        file.write(xml)


if __name__ == '__main__':
    main()

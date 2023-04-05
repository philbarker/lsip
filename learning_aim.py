import requests
from bs4 import BeautifulSoup
import json

API_ENDPOINT = 'https://submit-learner-data.service.gov.uk/find-a-learning-aim/LearningAimDetails/'


def lookup(ref: str):
    qualification = {}
    lookup_data = lookup_learning_aim(ref)
    qualification['LearnAimRef'] = ref
    qualification['LearnAimRefTitle'] = lookup_data['learningAimTitle']
    qualification['NotionalNVQLevelv2'] = lookup_data['Level']
    qualification['SectorSubjectAreaTier1'] = lookup_data['Sector subject area tier 1']
    qualification['SectorSubjectAreaTier2'] = lookup_data['Sector subject area tier 2']
    return qualification


def lookup_learning_aim(ref: str):
    """
    Look up a learning aim given a code
    :param ref: the reference id, typically 8 digits with optional letter
    :return: a dictionary of the properties of the learning aim
    """
    # pad with zeroes
    padded_ref = ref.zfill(8)

    url = API_ENDPOINT + padded_ref

    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')
    state = soup.find(id="initialState").text
    data = json.loads(state)

    data_elements = soup.findAll(attrs={"class": "govuk-summary-list__row"})
    for data_element in data_elements:
        key = data_element.find(attrs={"class": "govuk-summary-list__key"}).get_text().strip()
        value = data_element.find(attrs={"class": "govuk-summary-list__value"}).get_text().strip()
        data[key] = value
    return data







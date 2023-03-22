import requests
from bs4 import BeautifulSoup
import json

# This bit is a work in progress for pulling in FDs and L5s that aren't in the main learning aim open data, but
# are on the ILR website

API_ENDPOINT = 'https://submit-learner-data.service.gov.uk/find-a-learning-aim/LearningAimDetails/'
#document.getElementById("initialState").innerHTML
#    <div class="govuk-summary-list__row">
#                 <dt class="govuk-summary-list__key">
#                     Level
#                 </dt>
#                 <dd class="govuk-summary-list__value">
#                     Level 5
#                 </dd>
#             </div>

def lookup_learning_aim(ref:str):
    # pad with zeroes
    ref = ref.zfill(8)

    url = API_ENDPOINT + ref

    print(url)
    response = requests.get(url)
    print(response.text)

    soup = BeautifulSoup(response.text, 'html.parser')
    data = soup.find(id="initialState").text

    return json.loads(data)







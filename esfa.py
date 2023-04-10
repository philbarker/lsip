import os

import pandas as pd

#
# Constructs a CSV of existing open data for a provider
#


def keep_only(dataframe, columns):
    dataframe.drop(dataframe.columns.difference(columns), axis=1, inplace=True)


def load(csv_file=None, columns=None, remove_duplicates=True, as_str=None):
    df = None
    if as_str is not None:
        dtype = {}
        for item in as_str:
            dtype[item] = str
        df = pd.read_csv(csv_file, usecols=columns, dtype=dtype)
    else:
        df = pd.read_csv(csv_file, usecols=columns)
    if remove_duplicates:
        df = df.drop_duplicates()
    return df


def create_open_data(provider_ukprn=10000533, output_path='output' + os.sep + 'courses.csv'):
    # https://www.gov.uk/government/publications/sfa-course-directory
    esfa = pd.concat(
        map(
            pd.read_csv, ['data/ESFA_LiveCoursesWithRegionsAndVenuesReport-20220901.csv',
                          'data/ESFA_LiveCoursesWithRegionsAndVenuesReport-20230103.csv',
                          'data/ESFA_LiveCoursesWithRegionsAndVenuesReport-20230302.csv'
                          ]
        ),
        ignore_index=True)
    esfa['LEARN_AIM_REF'] = esfa['LEARN_AIM_REF'].astype('str')
    esfa['LEARN_AIM_REF'] = esfa['LEARN_AIM_REF'].apply(lambda x: x.zfill(8))

    fes = pd.read_csv('data/FES-fes-et-provider-enrolments-202223-q1.csv')

    quals = load(csv_file='data/LearningDelivery.csv', as_str=['LearnAimRef'])
    occupations = load(csv_file='data/soc2020.csv', columns=['SOC 2020', 'SOC 2020 UNIT GROUP DESCRIPTIONS'],
                       as_str=['SOC 2020'])

    levels = ['2', '3', '4', '5']

    # SOC lookups - taken from Barnet example
    # Merged with the SOC 2020 descriptions
    soc = load(csv_file='data/barnet_main.csv', columns=['Qualification', 'SOC 2020 Code'], as_str=['SOC 2020 Code'])
    soc = soc.merge(occupations, left_on='SOC 2020 Code', right_on='SOC 2020')
    keep_only(soc, ['Qualification', 'SOC 2020 Code', 'SOC 2020 UNIT GROUP DESCRIPTIONS'])

    # Subject lookups
    cols = ['SectorSubjectAreaTier1Desc', 'SectorSubjectAreaTier2Desc', 'SectorSubjectAreaTier1',
            'SectorSubjectAreaTier2']
    subjects = load(csv_file='data/SectorSubjectArea.csv')
    subjects = subjects[
        (subjects['SectorSubjectAreaTier2_EffTo'].isnull()) | (subjects['SectorSubjectAreaTier2_EffTo'] == u'')]
    subjects = subjects[
        (subjects['SectorSubjectAreaTier1_EffTo'].isnull()) | (subjects['SectorSubjectAreaTier1_EffTo'] == u'')]
    subjects.drop(subjects.columns.difference(cols), axis=1, inplace=True)
    subjects_l1 = subjects[['SectorSubjectAreaTier1', 'SectorSubjectAreaTier1Desc']]
    subjects_l1 = pd.DataFrame({c: subjects_l1[c].unique() for c in subjects_l1})

    # Qualifications
    quals = quals[(quals['EffectiveTo'].isnull()) | (quals['EffectiveTo'] == u'')]
    cols = ['LearnAimRef', 'LearnAimRefTitle', 'NotionalNVQLevelv2', 'SectorSubjectAreaTier1', 'SectorSubjectAreaTier2']
    keep_only(quals, cols)

    # Courses
    cols = ['PROVIDER_UKPRN', 'LEARN_AIM_REF', 'COURSE_NAME', 'COURSE_DESCRIPTION']
    esfa.drop(esfa.columns.difference(cols), axis=1, inplace=True)
    esfa = esfa.drop_duplicates()

    # Enrolments
    cols = ['time_period', 'provider_ukprn', 'level', 'ssa_t1_desc', 'enrols']
    fes = fes[(fes['level'].str.contains('|'.join(levels), regex=True))]
    keep_only(fes, cols)
    fes = fes[(fes['provider_ukprn'] == provider_ukprn)]
    fes = fes.merge(subjects_l1, left_on='ssa_t1_desc', right_on='SectorSubjectAreaTier1Desc')
    fes.to_csv('output/enrolments.csv')

    # Filter to Barnet
    courses = esfa[(esfa['PROVIDER_UKPRN'] == provider_ukprn)]

    # Join courses and qualifications
    courses = courses.merge(quals, left_on='LEARN_AIM_REF', right_on='LearnAimRef', how='left')

    # Join subjects
    courses = courses.merge(subjects, left_on='SectorSubjectAreaTier2', right_on='SectorSubjectAreaTier2', how='left')
    courses.drop('LearnAimRef', axis=1, inplace=True)

    # Filter out levels
    courses = courses[(courses['NotionalNVQLevelv2'].str.contains('|'.join(levels), regex=True, na=True))]

    # Join on SOC
    courses = courses.merge(soc, left_on='LEARN_AIM_REF', right_on='Qualification', how='left')

    # Output
    cols = ['PROVIDER_UKPRN', 'LEARN_AIM_REF', 'COURSE_NAME', 'COURSE_DESCRIPTION', 'LearnAimRefTitle',
            'NotionalNVQLevelv2', 'SectorSubjectAreaTier2', 'SectorSubjectAreaTier2Desc', 'SOC 2020 Code',
            'SOC 2020 UNIT GROUP DESCRIPTIONS']
    keep_only(courses, cols)
    courses.rename(columns=
    {
        'PROVIDER_UKPRN': "Provider.identifier",
        'LEARN_AIM_REF': "Qualification.identifier",
        'COURSE_NAME': "Course.name",
        'COURSE_DESCRIPTION': "Course.description",
        'LearnAimRefTitle': "Qualification.name",
        'NotionalNVQLevelv2': "Qualification.educationalLevel",
        'SectorSubjectAreaTier2': "Course.subject.code",
        'SectorSubjectAreaTier2Desc': "Course.subject.description",
        'SOC 2020 Code': "Qualification.occupation.code",
        'SOC 2020 UNIT GROUP DESCRIPTIONS': "Qualification.occupation.description"}
        , inplace=True)
    courses.to_csv(output_path)

    return courses

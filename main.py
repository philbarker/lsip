from learning_aim import lookup_learning_aim
import pandas as pd



def keep_only(dataframe, columns):
    dataframe.drop(dataframe.columns.difference(columns), axis=1, inplace=True)


def main():
    # https://www.gov.uk/government/publications/sfa-course-directory
    esfa = pd.concat(
        map(
            pd.read_csv, ['data/ESFA_LiveCoursesWithRegionsAndVenuesReport-20220901.csv',
                          'data/ESFA_LiveCoursesWithRegionsAndVenuesReport-20230103.csv',
                          'data/ESFA_LiveCoursesWithRegionsAndVenuesReport-20230302.csv'
                          ]
        ), ignore_index=True)
    #esfa = pd.read_csv('data/ESFA_LiveCoursesWithRegionsAndVenuesReport-20220901.csv')
    fes = pd.read_csv('data/FES-fes-et-provider-enrolments-202223-q1.csv')
    quals = pd.read_csv('data/LearningDelivery.csv')
    subjects = pd.read_csv('data/SectorSubjectArea.csv')

    levels = ['2','3','4','5']
    barnet = 10000533

    # SOC lookups
    soc = pd.read_csv('data/barnet_main.csv')
    cols=['Qualification', 'SOC 2020 Code']
    keep_only(soc, cols)
    soc = soc.drop_duplicates()

    # Subject lookups
    cols =['SectorSubjectAreaTier1Desc', 'SectorSubjectAreaTier2Desc', 'SectorSubjectAreaTier1', 'SectorSubjectAreaTier2']
    subjects = subjects[(subjects['SectorSubjectAreaTier2_EffTo'].isnull()) | (subjects['SectorSubjectAreaTier2_EffTo'] == u'')]
    subjects = subjects[(subjects['SectorSubjectAreaTier1_EffTo'].isnull()) | (subjects['SectorSubjectAreaTier1_EffTo'] == u'')]
    subjects.drop(subjects.columns.difference(cols), axis=1, inplace=True)
    subjects_l1 = subjects[['SectorSubjectAreaTier1', 'SectorSubjectAreaTier1Desc']]
    subjects_l1 = pd.DataFrame({c: subjects_l1[c].unique() for c in subjects_l1})

    # Qualifications
    quals = quals[(quals['EffectiveTo'].isnull()) | (quals['EffectiveTo'] == u'')]
    cols = ['LearnAimRef', 'LearnAimRefTitle', 'NotionalNVQLevelv2', 'SectorSubjectAreaTier1', 'SectorSubjectAreaTier2']
    quals.drop(quals.columns.difference(cols), axis=1, inplace=True)

    # Courses
    cols = ['PROVIDER_UKPRN', 'LEARN_AIM_REF', 'COURSE_NAME', 'COURSE_DESCRIPTION']
    #'COURSE_NAME', 'COURSE_DESCRIPTION', 'LOCATION_POSTCODE', 'COURSE_URL', 'DELIVER_MODE', 'STUDY_MODE', 'ATTENDANCE_PATTERN', 'DURATION_UNIT', 'DURATION_VALUE']
    esfa.drop(esfa.columns.difference(cols), axis=1, inplace=True)
    esfa = esfa.drop_duplicates()

    # Enrolments
    cols = ['time_period', 'provider_ukprn', 'level', 'ssa_t1_desc', 'enrols']
    fes = fes[(fes['level'].str.contains('|'.join(levels), regex=True))]
    fes.drop(fes.columns.difference(cols), axis=1, inplace=True)
    fes = fes[(fes['provider_ukprn'] == barnet)]
    fes = fes.merge(subjects_l1, left_on='ssa_t1_desc', right_on='SectorSubjectAreaTier1Desc')
    fes.to_csv('output/enrolments.csv')

    # Join courses and qualifications
    courses = esfa.merge(quals, left_on='LEARN_AIM_REF', right_on='LearnAimRef', how='left')
    courses = courses.merge(subjects, left_on='SectorSubjectAreaTier2', right_on='SectorSubjectAreaTier2', how='left')
    courses.drop('LearnAimRef', axis=1, inplace=True)

    # Filter out levels
    courses = courses[(courses['NotionalNVQLevelv2'].str.contains('|'.join(levels), regex=True, na=True))]

    # Filter to Barnet
    courses = courses[(courses['PROVIDER_UKPRN'] == barnet)]


    # Join on SOC
    courses = courses.merge(soc, left_on='LEARN_AIM_REF', right_on='Qualification', how='left')

    courses.to_csv('output/courses.csv')


if __name__ == '__main__':
    #print(lookup_learning_aim('303650'))
    main()


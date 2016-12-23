from datetime import date

import emotiv.models as models
from emotiv.database import db


def init_db():
    # This should never be called in production, alembic takes care of migration for us.
    try:
        print 'drop all tables'
        db.drop_all()
    except Exception, ex:
        print ex
    try:
        print 'create all tables'
        db.create_all()
        # Create default DB values.
        attr_gender = models.Attribute(name="Gender", input_type="ss")
        db.session.add(attr_gender)
        db.session.commit()
        gender_option = models.SelectOption(attribute=attr_gender, value="Male")
        db.session.add(gender_option)
        db.session.commit()
        attr_gender.possible_options.append(gender_option)
        db.session.commit()
        gender_option = models.SelectOption(attribute=attr_gender, value="Female")
        db.session.add(gender_option)
        db.session.commit()
        attr_gender.possible_options.append(gender_option)
        db.session.commit()
        gender_option = models.SelectOption(attribute=attr_gender, value="Prefer not to answer")
        db.session.add(gender_option)
        db.session.commit()
        attr_gender.possible_options.append(gender_option)
        db.session.commit()
        attr_education = models.Attribute(name="Highest level of completed education", input_type="ss")
        db.session.add(attr_education)
        db.session.commit()
        education_option = models.SelectOption(attribute=attr_education, value="None")
        db.session.add(education_option)
        db.session.commit()
        attr_education.possible_options.append(education_option)
        db.session.commit()
        education_option = models.SelectOption(attribute=attr_education, value="Elementary School")
        db.session.add(education_option)
        db.session.commit()
        attr_education.possible_options.append(education_option)
        db.session.commit()
        education_option = models.SelectOption(attribute=attr_education, value="Middle School")
        db.session.add(education_option)
        db.session.commit()
        attr_education.possible_options.append(education_option)
        db.session.commit()
        education_option = models.SelectOption(attribute=attr_education, value="High School")
        db.session.add(education_option)
        db.session.commit()
        attr_education.possible_options.append(education_option)
        db.session.commit()
        education_option = models.SelectOption(attribute=attr_education, value="Undergraduate")
        db.session.add(education_option)
        db.session.commit()
        attr_education.possible_options.append(education_option)
        db.session.commit()
        education_option = models.SelectOption(attribute=attr_education, value="Graduate")
        db.session.add(education_option)
        db.session.commit()
        attr_education.possible_options.append(education_option)
        db.session.commit()
        attr_dob = models.Attribute(name="Date Of Birth", input_type="dt")
        db.session.add(attr_dob)
        attr_political = models.Attribute(name="Political Beliefs", input_type="ss")
        db.session.add(attr_political)
        db.session.commit()
        political_option = models.SelectOption(attribute=attr_political, value="Very Conservative")
        db.session.add(political_option)
        db.session.commit()
        attr_political.possible_options.append(political_option)
        db.session.commit()
        political_option = models.SelectOption(attribute=attr_political, value="Conservative")
        db.session.add(political_option)
        db.session.commit()
        attr_political.possible_options.append(political_option)
        db.session.commit()
        political_option = models.SelectOption(attribute=attr_political, value="Moderate")
        db.session.add(political_option)
        db.session.commit()
        attr_political.possible_options.append(political_option)
        db.session.commit()
        political_option = models.SelectOption(attribute=attr_political, value="Liberal")
        db.session.add(political_option)
        db.session.commit()
        attr_political.possible_options.append(political_option)
        db.session.commit()
        political_option = models.SelectOption(attribute=attr_political, value="Very Liberal")
        db.session.add(political_option)
        db.session.commit()
        attr_political.possible_options.append(political_option)
        db.session.commit()
        attr_handedness = models.Attribute(name="Handedness", input_type="ss")
        db.session.add(attr_handedness)
        db.session.commit()
        handedness_option = models.SelectOption(attribute=attr_handedness, value="Left Handed")
        db.session.add(handedness_option)
        db.session.commit()
        attr_handedness.possible_options.append(handedness_option)
        db.session.commit()
        handedness_option = models.SelectOption(attribute=attr_handedness, value="Right Handed")
        db.session.add(handedness_option)
        db.session.commit()
        attr_handedness.possible_options.append(handedness_option)
        db.session.commit()
        handedness_option = models.SelectOption(attribute=attr_handedness, value="Ambidextrous")
        db.session.add(handedness_option)
        db.session.commit()
        attr_handedness.possible_options.append(handedness_option)
        db.session.commit()
        attr_location = models.Attribute(name="Location", input_type='ot')
        db.session.add(attr_location)
        db.session.commit()
        test_org = models.Organization(name='Emotiv', description='Emotiv')
        db.session.add(test_org)
        db.session.commit()
        test_user = models.User(email='emobuilder@bitrelay.io', active=True, builder=True, first_name='Test',
                                last_name='User', organization_id=test_org.id, username='emotiv_builder',
                                emotiv_dbapi_id=70943, emotiv_eoidc_id=71159,
                                emotiv_eoidc_username="eoidc_user_ZLtoYx0eqx2gs9G")
        db.session.add(test_user)
        db.session.commit()
        test_org.owner_id = test_user.id
        db.session.commit()
        new_request = models.RequestOrganization(organization_id=test_org.id, requester_id=test_user.id,
                                                 responder_id=test_user.id, response='a')
        db.session.add(new_request)
        db.session.commit()
        # Add test viewer
        test_viewer = models.User(email='emoviewer@bitrelay.io', active=True, builder=False, first_name='Test',
                                  last_name='User', username='emotiv_viewer', emotiv_dbapi_id=70944,
                                  emotiv_eoidc_id=71160, emotiv_eoidc_username="eoidc_user_AbRwejCpA5TOizN",
                                  organization_id=None)
        db.session.add(test_viewer)
        db.session.commit()
        test_admin = models.User(email='emoadmin@bitrelay.io', active=True, builder=True, first_name='Test',
                                 last_name='User', username='emotiv_admin', emotiv_dbapi_id=70957,
                                 emotiv_eoidc_id=71173, emotiv_eoidc_username="eoidc_user_AbRwejCpA5TOizN",
                                 organization_id=test_org.id)
        db.session.add(test_admin)
        db.session.commit()
        new_request = models.RequestOrganization(organization_id=test_org.id, requester_id=test_admin.id,
                                                 responder_id=test_user.id, response='a')
        db.session.add(new_request)
        db.session.commit()
        admin_role = models.Role(name='admin', description="Administration role.")
        db.session.add(admin_role)
        db.session.commit()
        test_admin.roles.append(admin_role)
        db.session.commit()
        test_experiment_criteria_1 = models.SelectOption.query.get(2)
        test_experiment_criteria_2 = models.SelectOption.query.get(5)
        test_user_attribute = models.UserAttribute(attribute_id=test_experiment_criteria_1.attribute_id,
                                                   user_id=test_viewer.id, value=test_experiment_criteria_1.value)
        db.session.add(test_user_attribute)
        db.session.commit()
        test_user_attribute = models.UserAttribute(attribute_id=test_experiment_criteria_2.attribute_id,
                                                   user_id=test_viewer.id, value=test_experiment_criteria_2.value)
        db.session.add(test_user_attribute)
        db.session.commit()
        # Add pending user
        test_pending = models.User(email='emopending@bitrelay.io', active=True, builder=True, first_name='Test',
                                   last_name='User', username='emotiv_pending', emotiv_dbapi_id=70945,
                                   emotiv_eoidc_id=71161, emotiv_eoidc_username="eoidc_user_GJqDxh9W7r8YNbj")
        db.session.add(test_pending)
        db.session.commit()
        new_request = models.RequestOrganization(organization_id=test_org.id, requester_id=test_pending.id,
                                                 response='p')
        db.session.add(new_request)
        db.session.commit()
        # test experiment
        test_experiment = models.Experiment(name="Test Experiment",
                                            organization=test_user.organization,
                                            description="A short little description, like this.",
                                            launch_date=date(2015, 1, 2),
                                            end_date=date(2016, 4, 3),
                                            private=False)

        def accept_select_option(experiment, option):
            f = (f for f in experiment.filters if f.parameters['attribute_id'] == option.attribute_id)
            _filter = next(f, None)
            if not _filter:
                _filter = models.Filter(
                    attribute=option.attribute,
                    experiment=experiment,
                    parameters={
                        'attribute_id': option.attribute_id,
                        'selected': [],
                    })
                db.session.add(_filter)
            _filter.parameters['selected'].append(option.id)
            db.session.commit()

        test_experiment.status = 'o'
        db.session.add(test_experiment)
        db.session.commit()
        accept_select_option(test_experiment, test_experiment_criteria_1)
        accept_select_option(test_experiment, test_experiment_criteria_2)
        test_experiment = models.Experiment(name="A Test Experiment",
                                            organization=test_user.organization,
                                            description="A short little description, like this.",
                                            launch_date=date(2015, 1, 1),
                                            end_date=date(2016, 4, 3),
                                            private=False)
        test_experiment.status = 'o'
        db.session.add(test_experiment)
        db.session.commit()
        accept_select_option(test_experiment, test_experiment_criteria_1)
        accept_select_option(test_experiment, test_experiment_criteria_2)
        test_experiment = models.Experiment(name="B Test Experiment",
                                            organization=test_user.organization,
                                            description="A short little description, like this.",
                                            launch_date=date(2014, 1, 2),
                                            end_date=date(2016, 4, 3))
        db.session.add(test_experiment)
        db.session.commit()
        accept_select_option(test_experiment, test_experiment_criteria_1)
        accept_select_option(test_experiment, test_experiment_criteria_2)
        db.session.commit()
        test_experiment = models.Experiment(name="C Test Experiment",
                                            organization=test_user.organization,
                                            description="A short little description, like this.",
                                            launch_date=date(2015, 12, 13),
                                            end_date=date(2016, 4, 3))
        test_experiment.status = 'o'
        db.session.add(test_experiment)
        db.session.commit()
        accept_select_option(test_experiment, test_experiment_criteria_1)
        accept_select_option(test_experiment, test_experiment_criteria_2)
        test_experiment = models.Experiment(name="D Test Experiment",
                                            organization=test_user.organization,
                                            description="A short little description, like this.",
                                            launch_date=date(2015, 11, 2),
                                            end_date=date(2016, 4, 3))
        test_experiment.status = 'p'
        db.session.add(test_experiment)
        db.session.commit()
        accept_select_option(test_experiment, test_experiment_criteria_1)
        accept_select_option(test_experiment, test_experiment_criteria_2)
        test_experiment = models.Experiment(name="E Test Experiment",
                                            organization=test_user.organization,
                                            description="A short little description, like this.",
                                            launch_date=date(2015, 9, 1),
                                            end_date=date(2016, 4, 3))
        test_experiment.status = 's'
        db.session.add(test_experiment)
        db.session.commit()
        accept_select_option(test_experiment, test_experiment_criteria_1)
        accept_select_option(test_experiment, test_experiment_criteria_2)
        test_experiment = models.Experiment(name="F Test Experiment",
                                            organization=test_user.organization,
                                            description="A short little description, like this.",
                                            launch_date=date(2015, 9, 11),
                                            end_date=date(2016, 4, 3))
        db.session.add(test_experiment)
        db.session.commit()
        accept_select_option(test_experiment, test_experiment_criteria_1)
        accept_select_option(test_experiment, test_experiment_criteria_2)
        test_experiment = models.Experiment(name="G Test Experiment",
                                            organization=test_user.organization,
                                            description="A short little description, like this.",
                                            launch_date=date(2015, 10, 21),
                                            end_date=date(2016, 4, 3))
        test_experiment.status = 's'
        db.session.add(test_experiment)
        db.session.commit()
        accept_select_option(test_experiment, test_experiment_criteria_1)
        accept_select_option(test_experiment, test_experiment_criteria_2)
        test_experiment = models.Experiment(name="H Test Experiment",
                                            organization=test_user.organization,
                                            description="A short little description, like this.",
                                            launch_date=date(2016, 11, 2),
                                            end_date=date(2016, 4, 3))
        test_experiment.status = 's'
        db.session.add(test_experiment)
        db.session.commit()
        accept_select_option(test_experiment, test_experiment_criteria_1)
        accept_select_option(test_experiment, test_experiment_criteria_2)
        test_experiment = models.Experiment(name="I Test Experiment",
                                            organization=test_user.organization,
                                            description="A short little description, like this.",
                                            launch_date=date(2016, 10, 5),
                                            end_date=date(2016, 4, 3))
        db.session.add(test_experiment)
        db.session.commit()
        accept_select_option(test_experiment, test_experiment_criteria_1)
        accept_select_option(test_experiment, test_experiment_criteria_2)
        print('all done')
    except Exception, ex:
        print ex.message

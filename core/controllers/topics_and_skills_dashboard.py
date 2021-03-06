# Copyright 2018 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Controllers for the topics and skills dashboard, from where topics and skills
are created.
"""

from core.controllers import base
from core.domain import acl_decorators
from core.domain import role_services
from core.domain import skill_domain
from core.domain import skill_services
from core.domain import topic_domain
from core.domain import topic_services
import feconf


class TopicsAndSkillsDashboardPage(base.BaseHandler):
    """Page showing the topics and skills dashboard."""

    @acl_decorators.can_access_topics_and_skills_dashboard
    def get(self):

        if not feconf.ENABLE_NEW_STRUCTURES:
            raise self.PageNotFoundException

        self.values.update({
            'nav_mode': feconf.NAV_MODE_TOPICS_AND_SKILLS_DASHBOARD
        })
        self.render_template(
            'pages/topics_and_skills_dashboard/'
            'topics_and_skills_dashboard.html', redirect_url_on_logout='/')


class TopicsAndSkillsDashboardPageDataHandler(base.BaseHandler):
    """Provides data for the user's topics and skills dashboard page."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON

    @acl_decorators.can_access_topics_and_skills_dashboard
    def get(self):
        """Handles GET requests."""

        topic_summaries = topic_services.get_all_topic_summaries()
        topic_summary_dicts = [
            summary.to_dict() for summary in topic_summaries]

        skill_summaries = skill_services.get_all_skill_summaries()
        skill_summary_dicts = [
            summary.to_dict() for summary in skill_summaries]

        topic_rights_dict = topic_services.get_all_topic_rights()
        for topic_summary in topic_summary_dicts:
            topic_rights = topic_rights_dict[topic_summary['id']]
            if topic_rights:
                topic_summary['is_published'] = (
                    topic_rights.topic_is_published)

        can_delete_topic = (
            role_services.ACTION_DELETE_TOPIC in self.user.actions)

        can_create_topic = (
            role_services.ACTION_CREATE_NEW_TOPIC in self.user.actions)

        can_create_skill = (
            role_services.ACTION_CREATE_NEW_SKILL in self.user.actions)

        self.values.update({
            'skill_summary_dicts': skill_summary_dicts,
            'topic_summary_dicts': topic_summary_dicts,
            'can_delete_topic': can_delete_topic,
            'can_create_topic': can_create_topic,
            'can_create_skill': can_create_skill
        })
        self.render_json(self.values)


class NewTopicHandler(base.BaseHandler):
    """Creates a new topic."""

    @acl_decorators.can_create_topic
    def post(self):
        """Handles POST requests."""
        if not feconf.ENABLE_NEW_STRUCTURES:
            raise self.PageNotFoundException
        name = self.payload.get('name')

        topic_domain.Topic.require_valid_name(name)
        new_topic_id = topic_services.get_new_topic_id()
        topic = topic_domain.Topic.create_default_topic(new_topic_id, name)
        topic_services.save_new_topic(self.user_id, topic)

        self.render_json({
            'topicId': new_topic_id
        })


class NewSkillHandler(base.BaseHandler):
    """Creates a new skill."""

    @acl_decorators.can_create_skill
    def post(self):
        if not feconf.ENABLE_NEW_STRUCTURES:
            raise self.PageNotFoundException
        topic_id = self.payload.get('topic_id')

        if topic_id is not None:
            topic = topic_services.get_topic_by_id(topic_id, strict=False)
            if topic is None:
                raise self.InvalidInputException

        description = self.payload.get('description')

        skill_domain.Skill.require_valid_description(description)

        new_skill_id = skill_services.get_new_skill_id()
        skill = skill_domain.Skill.create_default_skill(
            new_skill_id, description)
        skill_services.save_new_skill(self.user_id, skill)

        if topic_id is not None:
            topic_services.add_uncategorized_skill(
                self.user_id, topic_id, new_skill_id)

        self.render_json({
            'skillId': new_skill_id
        })

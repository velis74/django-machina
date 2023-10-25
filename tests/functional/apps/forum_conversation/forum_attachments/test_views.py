import os

import pytest
from django.urls import reverse
from faker import Faker

from machina.core.db.models import get_model
from machina.core.loading import get_class
from machina.test.factories import (
    AttachmentFactory, ForumReadTrackFactory, PostFactory, create_forum, create_topic
)
from machina.test.testcases import BaseClientTestCase


faker = Faker()

Attachment = get_model('forum_attachments', 'Attachment')
ForumReadTrack = get_model('forum_tracking', 'ForumReadTrack')
Post = get_model('forum_conversation', 'Post')
Topic = get_model('forum_conversation', 'Topic')
TopicReadTrack = get_model('forum_tracking', 'TopicReadTrack')

PermissionHandler = get_class('forum_permission.handler', 'PermissionHandler')
assign_perm = get_class('forum_permission.shortcuts', 'assign_perm')
remove_perm = get_class('forum_permission.shortcuts', 'remove_perm')


class TestAttachmentView(BaseClientTestCase):
    @pytest.fixture(autouse=True)
    def setup(self):
        # Permission handler
        self.perm_handler = PermissionHandler()

        # Set up a top-level forum
        self.top_level_forum = create_forum()

        # Set up a topic and some posts
        self.topic = create_topic(forum=self.top_level_forum, poster=self.user)
        self.post = PostFactory.create(topic=self.topic, poster=self.user)

        # Set up an attachment
        self.attachment = AttachmentFactory.create(post=self.post)

        # Mark the forum as read
        ForumReadTrackFactory.create(forum=self.top_level_forum, user=self.user)

        # Assign some permissions
        assign_perm('can_read_forum', self.user, self.top_level_forum)
        assign_perm('can_download_file', self.user, self.top_level_forum)

        yield

        # teardown
        # --

        attachments = Attachment.objects.all()
        for attachment in attachments:
            try:
                attachment.file.delete()
            except:  # noqa: E722
                pass

    def test_browsing_works(self):
        # Setup
        correct_url = reverse('forum_conversation:attachment', kwargs={'pk': self.attachment.id})
        # Run
        response = self.client.get(correct_url, follow=True)
        # Check
        assert response.status_code == 200

    def test_cannot_be_browsed_by_users_who_cannot_download_forum_files(self):
        # Setup
        remove_perm('can_download_file', self.user, self.top_level_forum)
        correct_url = reverse('forum_conversation:attachment', kwargs={'pk': self.attachment.id})
        # Run
        response = self.client.get(correct_url, follow=True)
        # Check
        assert response.status_code == 403

    def test_embed_the_correct_http_headers_in_the_response(self):
        # Setup
        correct_url = reverse('forum_conversation:attachment', kwargs={'pk': self.attachment.id})
        filename = os.path.basename(self.attachment.file.name)
        # Run
        response = self.client.get(correct_url, follow=True)
        # Check
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/plain'
        assert response['Content-Disposition'] == 'attachment; filename={}'.format(filename)

    def test_is_able_to_handle_unknown_file_content_types(self):
        # Setup
        attachment = AttachmentFactory.create(
            post=self.post, file__data='data')
        correct_url = reverse('forum_conversation:attachment', kwargs={'pk': attachment.id})
        # Run
        response = self.client.get(correct_url, follow=True)
        # Check
        assert response.status_code == 200
        assert response['Content-Type'] == 'text/plain'
        attachment.file.delete()

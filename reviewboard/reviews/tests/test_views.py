import os

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from reviewboard.attachments.models import FileAttachment
from reviewboard.reviews.models import (Comment, Review, ReviewRequest,
                                        ReviewRequestDraft, Screenshot)
    """Tests for views in reviewboard.reviews.views."""

        self.siteconfig.set('auth_require_sitewide_login', False)
        comment_text_1 = 'Comment text 1'
        comment_text_2 = 'Comment text 2'
        comment_text_3 = 'Comment text 3'
        comments = entry['comments']['diff_comments']
        """Testing visibility of file attachments on review requests"""
        comment_text_1 = 'Comment text 1'
        comment_text_2 = 'Comment text 2'
        review_request = ReviewRequest.objects.create(user1, None)
        filename = os.path.join(settings.STATIC_ROOT,
                                'rb', 'images', 'trophy.png')
        f = open(filename, 'r')
        file = SimpleUploadedFile(f.name, f.read(), content_type='image/png')
        f.close()

        file1 = FileAttachment.objects.create(caption=caption_1,
                                              file=file,
                                              mimetype='image/png')
        file2 = FileAttachment.objects.create(caption=caption_2,
                                              file=file,
                                              mimetype='image/png')
        review_request.file_attachments.add(file1)
        review_request.inactive_file_attachments.add(file2)
        # Create one on a draft with a new file attachment.
        draft = ReviewRequestDraft.create(review_request)
        file3 = FileAttachment.objects.create(caption=caption_3,
                                              file=file,
                                              mimetype='image/png')
        draft.file_attachments.add(file3)
        comments = entry['comments']['file_attachment_comments']
        """Testing visibility of screenshots on review requests"""
        comment_text_1 = 'Comment text 1'
        comment_text_2 = 'Comment text 2'
        review_request = ReviewRequest.objects.create(user1, None)
        screenshot1 = Screenshot.objects.create(caption=caption_1,
                                                image='')
        screenshot2 = Screenshot.objects.create(caption=caption_2,
                                                image='')
        review_request.screenshots.add(screenshot1)
        review_request.inactive_screenshots.add(screenshot2)
        # Create one on a draft with a new screenshot.
        draft = ReviewRequestDraft.create(review_request)
        screenshot3 = Screenshot.objects.create(caption=caption_3,
                                                image='')
        draft.screenshots.add(screenshot3)
        comments = entry['comments']['screenshot_comments']
        self.siteconfig.set('auth_require_sitewide_login', True)
            print('Error: %s' % self._get_context_var(response, 'error'))
            print('Error: %s' % self._get_context_var(response, 'error'))
        user = User.objects.get(username='doc')
        """Testing /diff/raw/ multiple Content-Disposition issue"""
        self.create_diffset(review_request=review_request, name='test, comma')
        filename = response['Content-Disposition']\
                           [len('attachment; filename='):]
    def _get_context_var(self, response, varname):
        for context in response.context:
            if varname in context:
                return context[varname]

        return None

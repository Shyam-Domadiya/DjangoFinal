"""
Test suite for Direct Messaging (Phase 3) models
Tests core functionality of DM system models
"""

import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from tweet.models import (
    Conversation, Message, ReadReceipt, TypingIndicator,
    MessageAttachment, ConversationMute, BlockedUserDM
)


class ConversationModelTests(TestCase):
    """Test Conversation model functionality"""

    def setUp(self):
        """Create test users"""
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')

    def test_conversation_creation(self):
        """Test creating a conversation between two users"""
        conv = Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2
        )
        self.assertEqual(conv.participant_1, self.user1)
        self.assertEqual(conv.participant_2, self.user2)
        self.assertFalse(conv.is_archived_by_p1)
        self.assertFalse(conv.is_muted_by_p1)

    def test_conversation_unique_constraint(self):
        """Test that only one conversation can exist between two users"""
        Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2
        )
        # Attempting to create another should fail
        with self.assertRaises(Exception):
            Conversation.objects.create(
                participant_1=self.user1,
                participant_2=self.user2
            )

    def test_get_other_participant(self):
        """Test getting the other participant in a conversation"""
        conv = Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2
        )
        self.assertEqual(conv.get_other_participant(self.user1), self.user2)
        self.assertEqual(conv.get_other_participant(self.user2), self.user1)

    def test_archive_conversation(self):
        """Test archiving a conversation for a user"""
        conv = Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2
        )
        conv.archive(self.user1)
        conv.refresh_from_db()
        self.assertTrue(conv.is_archived_by_p1)
        self.assertFalse(conv.is_archived_by_p2)

    def test_unarchive_conversation(self):
        """Test unarchiving a conversation"""
        conv = Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2,
            is_archived_by_p1=True
        )
        conv.unarchive(self.user1)
        conv.refresh_from_db()
        self.assertFalse(conv.is_archived_by_p1)

    def test_mute_conversation(self):
        """Test muting a conversation"""
        conv = Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2
        )
        conv.mute(self.user1)
        conv.refresh_from_db()
        self.assertTrue(conv.is_muted_by_p1)
        self.assertFalse(conv.is_muted_by_p2)

    def test_unmute_conversation(self):
        """Test unmuting a conversation"""
        conv = Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2,
            is_muted_by_p1=True
        )
        conv.unmute(self.user1)
        conv.refresh_from_db()
        self.assertFalse(conv.is_muted_by_p1)

    def test_block_user(self):
        """Test blocking a user in a conversation"""
        conv = Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2
        )
        conv.block_user(self.user1, self.user2)
        conv.refresh_from_db()
        self.assertTrue(conv.p1_blocked_p2)
        self.assertFalse(conv.p2_blocked_p1)

    def test_unblock_user(self):
        """Test unblocking a user"""
        conv = Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2,
            p1_blocked_p2=True
        )
        conv.unblock_user(self.user1, self.user2)
        conv.refresh_from_db()
        self.assertFalse(conv.p1_blocked_p2)

    def test_is_user_blocked(self):
        """Test checking if a user is blocked"""
        conv = Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2,
            p1_blocked_p2=True
        )
        self.assertTrue(conv.is_user_blocked(self.user1))
        self.assertFalse(conv.is_user_blocked(self.user2))

    def test_get_unread_count(self):
        """Test getting unread message count"""
        conv = Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2
        )
        # Create some messages
        Message.objects.create(
            conversation=conv,
            sender=self.user2,
            content='Hello',
            is_read=False
        )
        Message.objects.create(
            conversation=conv,
            sender=self.user2,
            content='How are you?',
            is_read=False
        )
        Message.objects.create(
            conversation=conv,
            sender=self.user1,
            content='Hi',
            is_read=False
        )
        
        # User1 should have 2 unread messages from user2
        self.assertEqual(conv.get_unread_count(self.user1), 2)
        # User2 should have 1 unread message from user1
        self.assertEqual(conv.get_unread_count(self.user2), 1)


class MessageModelTests(TestCase):
    """Test Message model functionality"""

    def setUp(self):
        """Create test data"""
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        self.conv = Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2
        )

    def test_message_creation(self):
        """Test creating a message"""
        msg = Message.objects.create(
            conversation=self.conv,
            sender=self.user1,
            content='Hello World'
        )
        self.assertEqual(msg.content, 'Hello World')
        self.assertEqual(msg.sender, self.user1)
        self.assertFalse(msg.is_read)
        self.assertFalse(msg.is_edited)
        self.assertFalse(msg.is_deleted)

    def test_mark_as_read(self):
        """Test marking a message as read"""
        msg = Message.objects.create(
            conversation=self.conv,
            sender=self.user1,
            content='Test'
        )
        self.assertFalse(msg.is_read)
        self.assertIsNone(msg.read_at)
        
        msg.mark_as_read()
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)
        self.assertIsNotNone(msg.read_at)

    def test_edit_content(self):
        """Test editing message content"""
        msg = Message.objects.create(
            conversation=self.conv,
            sender=self.user1,
            content='Original'
        )
        self.assertFalse(msg.is_edited)
        
        msg.edit_content('Edited')
        msg.refresh_from_db()
        self.assertEqual(msg.content, 'Edited')
        self.assertTrue(msg.is_edited)
        self.assertIsNotNone(msg.edited_at)

    def test_soft_delete(self):
        """Test soft deleting a message"""
        msg = Message.objects.create(
            conversation=self.conv,
            sender=self.user1,
            content='To delete'
        )
        self.assertFalse(msg.is_deleted)
        
        msg.soft_delete()
        msg.refresh_from_db()
        self.assertTrue(msg.is_deleted)

    def test_get_display_content(self):
        """Test getting display content"""
        msg = Message.objects.create(
            conversation=self.conv,
            sender=self.user1,
            content='Original'
        )
        self.assertEqual(msg.get_display_content(), 'Original')
        
        msg.soft_delete()
        self.assertEqual(msg.get_display_content(), '[deleted]')


class ReadReceiptModelTests(TestCase):
    """Test ReadReceipt model functionality"""

    def setUp(self):
        """Create test data"""
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        self.conv = Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2
        )
        self.msg = Message.objects.create(
            conversation=self.conv,
            sender=self.user1,
            content='Test'
        )

    def test_read_receipt_creation(self):
        """Test creating a read receipt"""
        receipt = ReadReceipt.objects.create(
            message=self.msg,
            reader=self.user2
        )
        self.assertEqual(receipt.message, self.msg)
        self.assertEqual(receipt.reader, self.user2)
        self.assertIsNotNone(receipt.read_at)

    def test_read_receipt_unique_constraint(self):
        """Test that only one receipt per message per reader"""
        ReadReceipt.objects.create(
            message=self.msg,
            reader=self.user2
        )
        with self.assertRaises(Exception):
            ReadReceipt.objects.create(
                message=self.msg,
                reader=self.user2
            )


class TypingIndicatorModelTests(TestCase):
    """Test TypingIndicator model functionality"""

    def setUp(self):
        """Create test data"""
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        self.conv = Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2
        )

    def test_typing_indicator_creation(self):
        """Test creating a typing indicator"""
        indicator = TypingIndicator.objects.create(
            conversation=self.conv,
            user=self.user1
        )
        self.assertEqual(indicator.conversation, self.conv)
        self.assertEqual(indicator.user, self.user1)
        self.assertIsNotNone(indicator.expires_at)

    def test_typing_indicator_is_active(self):
        """Test checking if typing indicator is active"""
        indicator = TypingIndicator.objects.create(
            conversation=self.conv,
            user=self.user1
        )
        self.assertTrue(indicator.is_active())
        
        # Set expiration to past
        indicator.expires_at = timezone.now() - timedelta(seconds=1)
        indicator.save()
        self.assertFalse(indicator.is_active())

    def test_typing_indicator_extend(self):
        """Test extending typing indicator expiration"""
        indicator = TypingIndicator.objects.create(
            conversation=self.conv,
            user=self.user1
        )
        # Set expiration to past to ensure extend makes it future
        indicator.expires_at = timezone.now() - timedelta(seconds=1)
        indicator.save()
        original_expires = indicator.expires_at
        
        indicator.extend()
        indicator.refresh_from_db()
        self.assertGreater(indicator.expires_at, original_expires)

    def test_typing_indicator_unique_constraint(self):
        """Test that only one typing indicator per user per conversation"""
        TypingIndicator.objects.create(
            conversation=self.conv,
            user=self.user1
        )
        with self.assertRaises(Exception):
            TypingIndicator.objects.create(
                conversation=self.conv,
                user=self.user1
            )


class MessageAttachmentModelTests(TestCase):
    """Test MessageAttachment model functionality"""

    def setUp(self):
        """Create test data"""
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        self.conv = Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2
        )
        self.msg = Message.objects.create(
            conversation=self.conv,
            sender=self.user1,
            content='Test'
        )

    def test_attachment_creation(self):
        """Test creating a message attachment"""
        attachment = MessageAttachment.objects.create(
            message=self.msg,
            file_type='image',
            file_size=1024,
            file_name='test.jpg'
        )
        self.assertEqual(attachment.message, self.msg)
        self.assertEqual(attachment.file_type, 'image')
        self.assertEqual(attachment.file_size, 1024)


class ConversationMuteModelTests(TestCase):
    """Test ConversationMute model functionality"""

    def setUp(self):
        """Create test data"""
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        self.conv = Conversation.objects.create(
            participant_1=self.user1,
            participant_2=self.user2
        )

    def test_conversation_mute_creation(self):
        """Test creating a conversation mute"""
        mute = ConversationMute.objects.create(
            user=self.user1,
            conversation=self.conv
        )
        self.assertEqual(mute.user, self.user1)
        self.assertEqual(mute.conversation, self.conv)

    def test_conversation_mute_unique_constraint(self):
        """Test that only one mute per user per conversation"""
        ConversationMute.objects.create(
            user=self.user1,
            conversation=self.conv
        )
        with self.assertRaises(Exception):
            ConversationMute.objects.create(
                user=self.user1,
                conversation=self.conv
            )


class BlockedUserDMModelTests(TestCase):
    """Test BlockedUserDM model functionality"""

    def setUp(self):
        """Create test data"""
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')

    def test_blocked_user_dm_creation(self):
        """Test creating a blocked user DM record"""
        blocked = BlockedUserDM.objects.create(
            blocker=self.user1,
            blocked_user=self.user2
        )
        self.assertEqual(blocked.blocker, self.user1)
        self.assertEqual(blocked.blocked_user, self.user2)

    def test_blocked_user_dm_unique_constraint(self):
        """Test that only one block per blocker per blocked user"""
        BlockedUserDM.objects.create(
            blocker=self.user1,
            blocked_user=self.user2
        )
        with self.assertRaises(Exception):
            BlockedUserDM.objects.create(
                blocker=self.user1,
                blocked_user=self.user2
            )

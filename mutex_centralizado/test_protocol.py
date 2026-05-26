import unittest
from protocol import format_message, parse_message, MessageType, MESSAGE_SIZE

class TestProtocol(unittest.TestCase):
    
    def test_format_message_request(self):
        msg = format_message(MessageType.REQUEST, 123)
        self.assertEqual(len(msg), MESSAGE_SIZE)
        self.assertTrue(msg.startswith("1|123|"))
        self.assertEqual(msg, "1|123|0000000000")
        
    def test_format_message_grant(self):
        msg = format_message(MessageType.GRANT, 42)
        self.assertEqual(len(msg), MESSAGE_SIZE)
        self.assertEqual(msg, "2|42|00000000000")
        
    def test_format_message_release(self):
        msg = format_message(MessageType.RELEASE, 9999)
        self.assertEqual(len(msg), MESSAGE_SIZE)
        self.assertEqual(msg, "3|9999|000000000")
        
    def test_parse_message_valid(self):
        msg_type, process_id = parse_message("1|123|0000000000")
        self.assertEqual(msg_type, MessageType.REQUEST)
        self.assertEqual(process_id, 123)
        
    def test_parse_message_invalid_size(self):
        with self.assertRaises(ValueError):
            parse_message("1|123|0")
            
    def test_format_message_too_large(self):
        # ID de processo que faria a string exceder MESSAGE_SIZE
        large_id = 10**16
        with self.assertRaises(ValueError):
            format_message(MessageType.REQUEST, large_id)

if __name__ == '__main__':
    unittest.main()

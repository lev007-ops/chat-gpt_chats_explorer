def test_explain_chat():
    messages = [
        Message(datetime=datetime(2021, 9, 1, 10, 0, 0), text="Hello", user="User1"),
        Message(datetime=datetime(2021, 9, 1, 11, 0, 0), text="How are you?", user="User2"),
        Message(datetime=datetime(2021, 9, 1, 12, 0, 0), text="I'm good, thanks!", user="User1"),
    ]
    context = [
        {"role": "assistant", "content": "Previous response from the assistant."},
    ]
    result = explain_chat(messages, context)
    assert isinstance(result, str)
    assert len(result) > 0

    # Add more test cases here

test_explain_chat()
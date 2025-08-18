# Feature: feedback endpoint API tests


#   Background:
#     Given The service is started locally
#       And REST API service hostname is localhost
#       And REST API service port is 8080
#       And REST API service prefix is /v1


#   Scenario: Check if feedback endpoint is working
#     Given The system is in default state
#      When I access endpoint "feedback" using HTTP POST with conversation ID conversationID
#           """
#           {
#               "llm_response": "bar",
#               "sentiment": -1,
#               "user_feedback": "Not satisfied with the response quality",
#               "user_question": "random question"
#           }
#           """
#      Then The status code of the response is 200
#      And The body of the response is the following
#           """
#           {"response": "feedback received"}
#           """

#   Scenario: Check if feedback endpoint is not working when not authorized
#     Given The system is in default state
#     And I remove the auth header
#      When I access endpoint "feedback" using HTTP POST with conversation ID conversationID
#           """
#           {
#               "llm_response": "bar",
#               "sentiment": -1,
#               "user_feedback": "Not satisfied with the response quality",
#               "user_question": "random question"
#           }
#           """
#      Then The status code of the response is 400
#      And The body of the response is the following
#           """
#           {"response": "feedback received"}
#           """

#   Scenario: Check if feedback endpoint is not working when feedback is disabled
#     Given The system is in default state
#     And I disable the feedback
#      When I access endpoint "feedback" using HTTP POST with conversation ID conversationID
#           """
#           {
#               "llm_response": "bar",
#               "sentiment": -1,
#               "user_feedback": "Not satisfied with the response quality",
#               "user_question": "random question"
#           }
#           """
#      Then The status code of the response is 403
#      And The body of the response is the following
#           """
#           {"response": "feedback received"}
#           """

#   Scenario: Check if feedback endpoint fails with incorrect body format when conversationID is not present
#     Given The system is in default state
#      When I access endpoint "feedback" using HTTP POST method
#           """
#           {
#               "llm_response": "bar",
#               "sentiment": -1,
#               "user_feedback": "Not satisfied with the response quality",
#               "user_question": "random question"
#           }
#           """
#      Then The status code of the response is 422
#      And The body of the response is the following
#           """
#           { "type": "missing", "loc": [ "body", "conversation_id" ], "msg": "Field required", }
#           """

#   Scenario: Check if feedback/status endpoint is working
#     Given The system is in default state
#      When I access REST API endpoint "feedback/status" using HTTP GET method
#      Then The status code of the response is 200
#      And The body of the response is the following
#           """
#           {"functionality": "feedback", "status": { "enabled": true}}
#           """



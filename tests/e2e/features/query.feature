# Feature: Query endpoint API tests
#TODO: fix test

#   Background:
#     Given The service is started locally
#       And REST API service hostname is localhost
#       And REST API service port is 8080
#       And REST API service prefix is /v1


#   Scenario: Check if LLM responds to sent question
#     Given The system is in default state
#      When I use "query" to ask question "Say hello"
#      Then The status code of the response is 200
#       And The response should have proper LLM response format
#       And The response should contain following fragments
#           | Fragments in LLM response |
#           | Hello                     |

#   Scenario: Check if LLM responds to sent question with different system prompt
#     Given The system is in default state
#     And I change the system prompt to "new system prompt"
#      When I use "query" to ask question "Say hello"
#      Then The status code of the response is 200
#       And The response should have proper LLM response format
#       And The response should contain following fragments
#           | Fragments in LLM response |
#           | Hello                     |

#   Scenario: Check if LLM responds with error for malformed request
#     Given The system is in default state
#     And I modify the request body by removing the "query"
#      When I use "query" to ask question "Say hello"
#      Then The status code of the response is 422
#       And The body of the response is the following
#           """
#           { "type": "missing", "loc": [ "body", "system_query" ], "msg": "Field required", }
#           """

#   Scenario: Check if LLM responds to sent question with error when not authenticated
#     Given The system is in default state
#      And I remove the auth header
#      When I use "query" to ask question "Say hello"
#      Then The status code of the response is 200
#       Then The status code of the response is 400
#       And The body of the response is the following
#           """
#           {"detail": "Unauthorized: No auth header found"}
#           """

#   Scenario: Check if LLM responds to sent question with error when not authorized
#       Given The system is in default state
#       And I modify the auth header so that the user is it authorized
#       When I use "query" to ask question "Say hello"
#       Then The status code of the response is 403
#       And The body of the response is the following
#           """
#           {"detail": "Forbidden: User is not authorized to access this resource"}
#           """
            
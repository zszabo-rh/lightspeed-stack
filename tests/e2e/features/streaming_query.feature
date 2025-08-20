# Feature: streaming_query endpoint API tests
#TODO: fix test

#   Background:
#     Given The service is started locally
#       And REST API service hostname is localhost
#       And REST API service port is 8080
#       And REST API service prefix is /v1


#   Scenario: Check if LLM responds to sent question
#     Given The system is in default state
#     And I use "streaming_query" to ask question "Say hello"
#      When I wait for the response to be completed
#      Then The status code of the response is 200
#       And The response should contain following fragments
#           | Fragments in LLM response |
#           | Hello                     |

#   Scenario: Check if LLM responds to sent question with different system prompt
#     Given The system is in default state
#     And I change the system prompt to "new system prompt"
#     And I use "streaming_query" to ask question "Say hello"
#      When I wait for the response to be completed
#      Then The status code of the response is 200
#       And The response should contain following fragments
#           | Fragments in LLM response |
#           | Hello                     |

#   Scenario: Check if LLM responds for streaming_query request with error for malformed request
#     Given The system is in default state
#     And I modify the request body by removing the "query"
#     And I use "streaming_query" to ask question "Say hello"
#      When I wait for the response to be completed
#      Then The status code of the response is 422
#       And The body of the response is the following
#           """
#           { "type": "missing", "loc": [ "body", "system_query" ], "msg": "Field required", }
#           """

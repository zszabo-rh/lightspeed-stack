# Feature: conversations endpoint API tests
#TODO: fix test

#   Background:
#     Given The service is started locally
#       And REST API service hostname is localhost
#       And REST API service port is 8080
#       And REST API service prefix is /v1


#   Scenario: Check if conversations endpoint finds the correct conversation when it exists
#     Given The system is in default state
#      When I access REST API endpoint "conversations" using HTTP GET method
#      Then The status code of the response is 200
#      And the proper conversation is returned

#   Scenario: Check if conversations endpoint does not finds the conversation when it does not exists
#     Given The system is in default state
#      When I access REST API endpoint "conversations" using HTTP GET method
#      Then The status code of the response is 404

#   Scenario: Check if conversations endpoint fails when conversation id is not provided
#     Given The system is in default state
#      When I access REST API endpoint "conversations" using HTTP GET method
#      Then The status code of the response is 422

#   Scenario: Check if conversations endpoint fails when service is unavailable
#     Given The system is in default state
#     And the service is stopped
#      When I access REST API endpoint "conversations" using HTTP GET method
#      Then The status code of the response is 503

#   Scenario: Check if conversations/delete endpoint finds the correct conversation when it exists
#     Given The system is in default state
#      When I access REST API endpoint "conversations/delete" using HTTP GET method
#      Then The status code of the response is 200
#      And the deleted conversation is not found

#   Scenario: Check if conversations/delete endpoint does not finds the conversation when it does not exists
#     Given The system is in default state
#      When I access REST API endpoint "conversations/delete" using HTTP GET method
#      Then The status code of the response is 404

#   Scenario: Check if conversations/delete endpoint fails when conversation id is not provided
#     Given The system is in default state
#      When I access REST API endpoint "conversations/delete" using HTTP GET method
#      Then The status code of the response is 422

#   Scenario: Check if conversations/delete endpoint fails when service is unavailable
#     Given The system is in default state
#     And the service is stopped
#      When I access REST API endpoint "conversations/delete" using HTTP GET method
#      Then The status code of the response is 503


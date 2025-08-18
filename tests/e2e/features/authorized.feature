# Feature: Authorized endpoint API tests
# TODO: fix test

#   Background:
#     Given The service is started locally
#       And REST API service hostname is localhost
#       And REST API service port is 8080
#       And REST API service prefix is /v1

#   Scenario: Check if the OpenAPI endpoint works as expected
#     Given The system is in default state
#      When I access endpoint "authorized" using HTTP POST method
#      Then The status code of the response is 200
#       And The body of the response has proper username

#   Scenario: Check if LLM responds to sent question with error when not authenticated
#     Given The system is in default state
#      And I remove the auth header
#      When I access endpoint "authorized" using HTTP POST method
#      Then The status code of the response is 400
#      And The body of the response is the following
#           """
#           {"detail": "Unauthorized: No auth header found"}
#           """

#   Scenario: Check if LLM responds to sent question with error when not authorized
#     Given The system is in default state
#      And I modify the auth header so that the user is it authorized
#      When I access endpoint "authorized" using HTTP POST method
#      Then The status code of the response is 403
#      And The body of the response is the following
#           """
#           {"detail": "Forbidden: User is not authorized to access this resource"}
#           """

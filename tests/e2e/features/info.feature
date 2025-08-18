# Feature: Info endpoint API tests
#TODO: fix test

#   Background:
#     Given The service is started locally
#       And REST API service hostname is localhost
#       And REST API service port is 8080
#       And REST API service prefix is /v1

#   Scenario: Check if the OpenAPI endpoint works as expected
#     Given The system is in default state
#      When I access endpoint "openapi.json" using HTTP GET method
#      Then The status code of the response is 200
#       And The body of the response contains OpenAPI

#   Scenario: Check if info endpoint is working
#     Given The system is in default state
#      When I access REST API endpoint "info" using HTTP GET method
#      Then The status code of the response is 200
#       And The body of the response has proper name "lightspeed_stack" and version "0.2.0"

#   Scenario: Check if models endpoint is working
#     Given The system is in default state
#      When I access REST API endpoint "models" using HTTP GET method
#      Then The status code of the response is 200
#       And The body of the response contains gpt


#   Scenario: Check if models endpoint is working
#     Given The system is in default state
#     And The llama-stack connection is disrupted
#      When I access REST API endpoint "models" using HTTP GET method
#      Then The status code of the response is 503

#   Scenario: Check if metrics endpoint is working
#     Given The system is in default state
#      When I access REST API endpoint "metrics" using HTTP GET method
#      Then The status code of the response is 200
#      And The body of the response has proper metrics

#   Scenario: Check if metrics endpoint is working
#     Given The system is in default state
#     And  The llama-stack connection is disrupted
#      When I access REST API endpoint "metrics" using HTTP GET method
#      Then The status code of the response is 500
 

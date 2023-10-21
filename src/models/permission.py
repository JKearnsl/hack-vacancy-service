from enum import Enum


class Permission(Enum):
    GET_PUBLIC_VACANCY = "GET_PUBLIC_VACANCY"

    # User
    GET_TESTING = "GET_TESTING"
    START_TESTING = "START_TESTING"
    COMPLETE_TESTING = "COMPLETE_TESTING"
    GET_SELF_TEST_RESULTS = "GET_TEST_RESULTS"

    # HR
    GET_PRIVATE_VACANCY = "GET_PRIVATE_VACANCY"
    CREATE_VACANCY = "CREATE_VACANCY"
    UPDATE_VACANCY = "UPDATE_VACANCY"
    DELETE_VACANCY = "DELETE_VACANCY"

    CREATE_TESTING = "CREATE_TESTING"
    UPDATE_TESTING = "UPDATE_TESTING"
    DELETE_TESTING = "DELETE_TESTING"
    GET_USER_TEST_RESULTS = "GET_USER_TEST_RESULTS"
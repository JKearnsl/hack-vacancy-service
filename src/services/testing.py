import uuid
from datetime import datetime, timedelta
from typing import Literal

from src import exceptions
from src.models import schemas
from src.models.auth import BaseUser
from src.models.permission import Permission
from src.models.state import VacancyState, UserState
from src.services.auth.filters import permission_filter
from src.services.auth.filters import state_filter
from src.services.repository import AttemptRepo, VacancyRepo, PracticalQuestionRepo, TheoreticalQuestionRepo
from src.services.repository import TestingRepo


class TestingApplicationService:

    def __init__(
            self,
            current_user: BaseUser,
            testing_repo: TestingRepo,
            attempt_repo: AttemptRepo,
            vacancy_repo: VacancyRepo,
            practical_question_repo: PracticalQuestionRepo,
            theoretical_question_repo: TheoreticalQuestionRepo,
    ):
        self._current_user = current_user
        self._repo = testing_repo
        self._attempt_repo = attempt_repo
        self._vacancy_repo = vacancy_repo
        self._practical_question_repo = practical_question_repo
        self._theoretical_question_repo = theoretical_question_repo

    @permission_filter(Permission.GET_SELF_TEST_RESULTS)
    @state_filter(UserState.ACTIVE)
    async def get_test_attempts(
            self,
            testing_id: uuid.UUID = None,
            page: int = 1,
            per_page: int = 10,
            order_by: Literal["title", "created_at"] = "created_at",
    ) -> list[schemas.AttemptTest]:
        """
        Получить список попыток прохождения теста текущего пользователя

        :param testing_id: id тестирования
        :param page: номер страницы (всегда >= 1)
        :param per_page: количество статей на странице (всегда >= 1, но <= per_page_limit)
        :param order_by: поле сортировки
        :return:

        """

        if page < 1:
            raise exceptions.NotFound("Страница не найдена")
        if per_page < 1:
            raise exceptions.BadRequest("Неверное количество элементов на странице")

        per_page_limit = 40

        # Подготовка входных данных
        per_page = min(per_page, per_page_limit, 2147483646)
        offset = min((page - 1) * per_page, 2147483646)

        # Выполнение запроса
        attempts = await self._attempt_repo.get_all(
            limit=per_page,
            offset=offset,
            order_by=order_by,
            user_id=self._current_user.id,
            **{"testing_id": testing_id}
        )
        return [schemas.AttemptTest.model_validate(attempt) for attempt in attempts]

    @permission_filter(Permission.GET_USER_TEST_RESULTS)
    @state_filter(UserState.ACTIVE)
    async def get_user_attempts(
            self,
            page: int = 1,
            per_page: int = 10,
            order_by: Literal["title", "created_at"] = "created_at",
            query: str = None,
            user_id: uuid.UUID = None
    ) -> list[schemas.AttemptTest]:
        """
        Получить общий список удачных попыток прохождения тестирования пользователей

        :param page: номер страницы (всегда >= 1)
        :param per_page: количество статей на странице (всегда >= 1, но <= per_page_limit)
        :param order_by: поле сортировки
        :param query: строка поиска
        :param user_id: id пользователя

        :return:

        """

        if page < 1:
            raise exceptions.NotFound("Страница не найдена")
        if per_page < 1:
            raise exceptions.BadRequest("Неверное количество элементов на странице")

        per_page_limit = 40

        # Подготовка входных данных
        per_page = min(per_page, per_page_limit, 2147483646)
        offset = min((page - 1) * per_page, 2147483646)

        # Выполнение запроса
        if query:
            attempts = await self._attempt_repo.search(
                limit=per_page,
                offset=offset,
                order_by=order_by,
                query=query,
                **{"user_id": user_id}
            )
        else:
            attempts = await self._attempt_repo.get_all(
                limit=per_page,
                offset=offset,
                order_by=order_by,
                **{"user_id": user_id}
            )
        return [schemas.AttemptTest.model_validate(attempt) for attempt in attempts]

    @permission_filter(Permission.START_TESTING)
    @state_filter(UserState.ACTIVE)
    async def start_practical_testing(self, testing_id: uuid.UUID) -> list[schemas.PracticalQuestion]:
        """
        Начать практическое тестирование

        :param testing_id: id тестирования
        :return:

        """
        # Проверка наличия тестирования
        testing = await self._repo.get(id=testing_id)
        if not testing:
            raise exceptions.NotFound(f"Тестирование с id:{testing_id} не найдено")

        vacancy = await self._vacancy_repo.get(id=testing.vacancy_id)
        if not vacancy:
            raise exceptions.NotFound(f"Вакансия с id:{testing.vacancy_id} не найдена")

        if vacancy.state != VacancyState.OPENED:
            raise exceptions.BadRequest(f"Вакансия с id:{testing.vacancy_id} не открыта")

        first_attempt = await self._attempt_repo.get_first(
            user_id=self._current_user.id,
            test_id=testing_id
        )

        if first_attempt:
            time_now = datetime.now()
            time_deadline = first_attempt.created_at + timedelta(days=vacancy.test_time)

            if time_now > time_deadline:
                raise exceptions.BadRequest(f"Время прохождения теста истекло")

        questions = await self._practical_question_repo.get_all(testing_id=testing_id)
        return [schemas.PracticalQuestion.model_validate(question) for question in questions]

    @permission_filter(Permission.START_TESTING)
    @state_filter(UserState.ACTIVE)
    async def start_theoretical_testing(self, testing_id: uuid.UUID) -> list[schemas.TheoreticalQuestion]:
        """
        Начать теоретическое тестирование

        :param testing_id: id тестирования
        :return:

        """
        # Проверка наличия тестирования
        testing = await self._repo.get(id=testing_id)
        if not testing:
            raise exceptions.NotFound(f"Тестирование с id:{testing_id} не найдено")

        vacancy = await self._vacancy_repo.get(id=testing.vacancy_id)
        if not vacancy:
            raise exceptions.NotFound(f"Вакансия с id:{testing.vacancy_id} не найдена")

        if vacancy.state != VacancyState.OPENED:
            raise exceptions.BadRequest(f"Вакансия с id:{testing.vacancy_id} не открыта")

        first_attempt = await self._attempt_repo.get_first(
            user_id=self._current_user.id,
            test_id=testing_id
        )

        if first_attempt:
            time_now = datetime.now()
            time_deadline = first_attempt.created_at + timedelta(days=vacancy.test_time)

            if time_now > time_deadline:
                raise exceptions.BadRequest(f"Время прохождения теста истекло")

        questions = await self._theoretical_question_repo.get_all(testing_id=testing_id)
        return [schemas.TheoreticalQuestion.model_validate(question) for question in questions]

    @permission_filter(Permission.COMPLETE_TESTING)
    @state_filter(UserState.ACTIVE)
    async def complete_theoretical_testing(
            self,
            testing_id: uuid.UUID,
            data: list[schemas.AnswerToTheoreticalQuestion]
    ) -> schemas.AttemptTest:
        """
        Завершить теоретическое тестирование

        :param testing_id: id тестирования
        :param data: данные прохождения тестирования
        :return:

        """
        # Проверка наличия тестирования
        testing = await self._repo.get(id=testing_id)
        if not testing:
            raise exceptions.NotFound(f"Тестирование с id:{testing_id} не найдено")

        vacancy = await self._vacancy_repo.get(id=testing.vacancy_id)
        if not vacancy:
            raise exceptions.NotFound(f"Вакансия с id:{testing.vacancy_id} не найдена")

        if vacancy.state != VacancyState.OPENED:
            raise exceptions.BadRequest(f"Вакансия с id:{testing.vacancy_id} не открыта")

        first_attempt = await self._attempt_repo.get_first(
            user_id=self._current_user.id,
            test_id=testing_id
        )

        if first_attempt:
            time_now = datetime.now()
            time_deadline = first_attempt.created_at + timedelta(days=vacancy.test_time)

            if time_now > time_deadline:
                raise exceptions.BadRequest(f"Время прохождения теста истекло")

        questions = await self._theoretical_question_repo.get_all(testing_id=testing_id)
        correct_answers = 0

        # todo

        attempt = schemas.AttemptTest.model_validate(
            await self._attempt_repo.create(
                user_id=self._current_user.id,
                testing_id=testing_id,
                correct_answers=correct_answers,
                total_answers=len(questions)
            )
        )

        return schemas.AttemptTest(**attempt.model_dump(), test=schemas.Testing.model_validate(testing))

    @permission_filter(Permission.COMPLETE_TESTING)
    @state_filter(UserState.ACTIVE)
    async def complete_practical_testing(
            self,
            testing_id: uuid.UUID,
            data: list[schemas.AnswerToPracticalQuestion]
    ) -> schemas.AttemptTest:
        """
        Завершить практическое тестирование

        :param testing_id: id тестирования
        :param data: данные прохождения тестирования
        :return:

        """
        # Проверка наличия тестирования
        testing = await self._repo.get(id=testing_id)
        if not testing:
            raise exceptions.NotFound(f"Тестирование с id:{testing_id} не найдено")

        vacancy = await self._vacancy_repo.get(id=testing.vacancy_id)
        if not vacancy:
            raise exceptions.NotFound(f"Вакансия с id:{testing.vacancy_id} не найдена")

        if vacancy.state != VacancyState.OPENED:
            raise exceptions.BadRequest(f"Вакансия с id:{testing.vacancy_id} не открыта")

        first_attempt = await self._attempt_repo.get_first(
            user_id=self._current_user.id,
            test_id=testing_id
        )

        if first_attempt:
            time_now = datetime.now()
            time_deadline = first_attempt.created_at + timedelta(days=vacancy.test_time)

            if time_now > time_deadline:
                raise exceptions.BadRequest(f"Время прохождения теста истекло")

        questions = await self._practical_question_repo.get_all(testing_id=testing_id)
        correct_answers = 0

        # todo

        attempt = schemas.AttemptTest.model_validate(
            await self._attempt_repo.create(
                user_id=self._current_user.id,
                testing_id=testing_id,
                correct_answers=correct_answers,
                total_answers=len(questions)
            )
        )
        return schemas.AttemptTest(**attempt.model_dump(), test=schemas.Testing.model_validate(testing))

    @permission_filter(Permission.CREATE_TESTING)
    @state_filter(UserState.ACTIVE)
    async def create_testing(self, vacancy_id: uuid.UUID, data: schemas.TestingCreate) -> schemas.Testing:
        """
        Создать тестирование

        :param vacancy_id: id вакансии
        :param data: данные тестирования
        :return:

        """
        vacancy = await self._vacancy_repo.get(id=vacancy_id)
        if not vacancy:
            raise exceptions.NotFound(f"Вакансия с id:{vacancy_id} не найдена")

        if vacancy.state != VacancyState.OPENED:
            raise exceptions.BadRequest(f"Вакансия с id:{vacancy_id} не открыта")

        testing = await self._repo.create(**data.model_dump(), vacancy_id=vacancy_id)
        return schemas.Testing.model_validate(testing)

    @permission_filter(Permission.UPDATE_TESTING)
    @state_filter(UserState.ACTIVE)
    async def update_testing(self, testing_id: uuid.UUID, data: schemas.TestingUpdate) -> schemas.Testing:
        """
        Обновить тестирование

        :param testing_id: id тестирования
        :param data: данные тестирования
        :return:

        """
        testing = await self._repo.get(id=testing_id)
        if not testing:
            raise exceptions.NotFound(f"Тестирование с id:{testing_id} не найдено")

        vacancy = await self._vacancy_repo.get(id=testing.vacancy_id)
        if not vacancy:
            raise exceptions.NotFound(f"Вакансия с id:{testing.vacancy_id} не найдена")

        if vacancy.state != VacancyState.OPENED:
            raise exceptions.BadRequest(f"Вакансия с id:{testing.vacancy_id} не открыта")

        await self._repo.update(testing_id, **data.model_dump(exclude_unset=True))
        testing = await self._repo.get(id=testing_id)
        return schemas.Testing.model_validate(testing)

    @permission_filter(Permission.DELETE_TESTING)
    @state_filter(UserState.ACTIVE)
    async def delete_testing(self, testing_id: uuid.UUID) -> None:
        """
        Удалить тестирование

        :param testing_id: id тестирования
        :return:

        """
        testing = await self._repo.get(id=testing_id)
        if not testing:
            raise exceptions.NotFound(f"Тестирование с id:{testing_id} не найдено")

        vacancy = await self._vacancy_repo.get(id=testing.vacancy_id)
        if not vacancy:
            raise exceptions.NotFound(f"Вакансия с id:{testing.vacancy_id} не найдена")

        if vacancy.state != VacancyState.OPENED:
            raise exceptions.BadRequest(f"Вакансия с id:{testing.vacancy_id} не открыта")
        # todo
        await self._repo.delete(id=testing_id)

    @permission_filter(Permission.GET_TESTING)
    @state_filter(UserState.ACTIVE)
    async def get_testing(self, testing_id: uuid.UUID) -> schemas.Testing:
        """
        Получить тестирование

        :param testing_id: id тестирования
        :return:

        """
        testing = await self._repo.get(id=testing_id)
        if not testing:
            raise exceptions.NotFound(f"Тестирование с id:{testing_id} не найдено")

        vacancy = await self._vacancy_repo.get(id=testing.vacancy_id)
        if not vacancy:
            raise exceptions.NotFound(f"Вакансия с id:{testing.vacancy_id} не найдена")

        if vacancy.state != VacancyState.OPENED:
            raise exceptions.BadRequest(f"Вакансия с id:{testing.vacancy_id} не открыта")

        return schemas.Testing.model_validate(testing)

    @permission_filter(Permission.GET_TESTING)
    @state_filter(UserState.ACTIVE)
    async def get_testings(self, vacancy_id: uuid.UUID, ) -> list[schemas.Testing]:
        """
        Получить список тестирований вакансии

        :param vacancy_id: id вакансии
        :return:

        """

        testings = await self._repo.get_all(vacancy_id=vacancy_id)
        return [schemas.Testing.model_validate(testing) for testing in testings]
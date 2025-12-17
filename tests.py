import pytest
from main import Parser


class TestParser:
    def setup_method(self):
        self.parser = Parser()

    # 1. Тест парсинга чисел
    def test_parse_numbers(self):
        assert self.parser.parse_number("123") == 123
        assert self.parser.parse_number("-456") == -456

    # 2. Тест парсинга простых массивов
    def test_parse_arrays_simple(self):
        # Простой массив без пробелов
        result = self.parser.parse_array("1,2,3")
        assert result == [1, 2, 3]

    # 3. Тест парсинга простых словарей
    def test_parse_dicts_simple(self):
        result = self.parser.parse_dict("a=1,b=2")
        assert result == {"a": 1, "b": 2}

    # 4. Тест объявления и использования констант
    def test_constants_simple(self):
        content = "def maxconn := 100\n{connections=?[maxconn]}"
        result = self.parser.parse_file(content)
        assert "connections = 100" in result

    # 5. Тест вложенных структур
    def test_nested_structures_simple(self):
        content = "{server={port=8080}}"
        result = self.parser.parse_file(content)
        assert "[server]" in result
        assert "port = 8080" in result

    # 6. Тест массива в словаре
    def test_dict_with_array_simple(self):
        content = "{port=<<80>>}"
        result = self.parser.parse_file(content)
        assert "port = [80]" in result

    # 7. Тест словаря в словаре
    def test_dict_in_dict(self):
        content = "{config={timeout=30}}"
        result = self.parser.parse_file(content)
        assert "[config]" in result
        assert "timeout = 30" in result

    # 8. Тест константы как массива
    def test_constant_array_simple(self):
        content = "def port := <<80>>\n{listen=?[port]}"
        result = self.parser.parse_file(content)
        assert "listen = [80]" in result

    # 9. Тест комментариев
    def test_comments(self):
        content = "def port := 8080\n{server=?[port]}"
        result = self.parser.parse_file(content)
        assert "server = 8080" in result

    # 10. Тест полного примера (без массива)
    def test_complete_example_no_array(self):
        content = "def workers := 4\ndef timeout := 30\n{server={maxworkers=?[workers],timeout=?[timeout]}}"
        result = self.parser.parse_file(content)
        assert "[server]" in result
        assert "maxworkers = 4" in result
        assert "timeout = 30" in result

    # 11. Тест ошибки - неопределенная константа
    def test_error_undefined_constant(self):
        content = "{x=?[unknown]}"
        with pytest.raises(SyntaxError, match="Неопределенная константа"):
            self.parser.parse_file(content)

    # 12. Тест ошибки - некорректное имя
    def test_error_invalid_name(self):
        content = "{123abc=1}"
        with pytest.raises(SyntaxError, match="Некорректное имя"):
            self.parser.parse_file(content)

    # 13. Тест ошибки - несколько корневых словарей
    def test_error_multiple_dicts(self):
        content = "{a=1}"
        result = self.parser.parse_file(content)
        assert "a = 1" in result

    # 14. Тест ошибки - незакрытый словарь
    def test_error_unclosed_dict(self):
        content = "{a=1"
        with pytest.raises(SyntaxError, match="должен быть завершен"):
            self.parser.parse_file(content)
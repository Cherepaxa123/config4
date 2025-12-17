import sys
import re
import argparse
from typing import Dict, Any, List
from pathlib import Path


class Parser:
    def __init__(self):
        self.constants: Dict[str, Any] = {}
        self.output_lines: List[str] = []

    def parse_number(self, token: str) -> int:
        return int(token)

    def parse_array(self, content: str) -> List[Any]:
        if not content.strip():
            return []

        values = []
        parts = []
        current = ""
        depth = 0

        for char in content:
            if char == "<" and current.endswith("<"):
                depth += 1
                current = current[:-1] + "<<"
            elif char == ">" and current.endswith(">"):
                depth -= 1
                current = current[:-1] + ">>"
            elif char == "{":
                depth += 1
                current += char
            elif char == "}":
                depth -= 1
                current += char
            elif char == "," and depth == 0:
                parts.append(current.strip())
                current = ""
            else:
                current += char

        if current.strip():
            parts.append(current.strip())

        for part in parts:
            if part:
                values.append(self.parse_value(part.strip()))

        return values

    def parse_dict(self, content: str) -> Dict[str, Any]:
        result = {}
        content = content.strip()

        if not content:
            return result

        parts = []
        current = ""
        depth = 0

        for char in content:
            if char == "<" and current.endswith("<"):
                depth += 1
                current = current[:-1] + "<<"
            elif char == ">" and current.endswith(">"):
                depth -= 1
                current = current[:-1] + ">>"
            elif char == "{":
                depth += 1
                current += char
            elif char == "}":
                depth -= 1
                current += char
            elif char == "," and depth == 0:
                parts.append(current.strip())
                current = ""
            else:
                current += char

        if current.strip():
            parts.append(current.strip())

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if "=" not in part:
                raise SyntaxError(f"Некорректное определение: {part}")

            name, value = part.split("=", 1)
            name = name.strip()
            value = value.strip()

            if not re.fullmatch(r"[a-z]+", name):
                raise SyntaxError(f"Некорректное имя '{name}'")

            result[name] = self.parse_value(value)

        return result

    def parse_value(self, value_str: str) -> Any:
        value_str = value_str.strip()

        if value_str.startswith("?[") and value_str.endswith("]"):
            const_name = value_str[2:-1].strip()
            if const_name not in self.constants:
                raise SyntaxError(f"Неопределенная константа: {const_name}")
            return self.constants[const_name]

        # Числа
        if re.fullmatch(r"[+-]?\d+", value_str):
            return self.parse_number(value_str)

        # Массивы
        if value_str.startswith("<<") and value_str.endswith(">>"):
            return self.parse_array(value_str[2:-2])

        # Словари
        if value_str.startswith("{") and value_str.endswith("}"):
            return self.parse_dict(value_str[1:-1])

        # Идентификаторы
        if re.fullmatch(r"[a-z]+", value_str):
            raise SyntaxError(f"Неизвестный идентификатор: {value_str}")

        raise SyntaxError(f"Некорректное значение: {value_str}")

    def parse_file(self, content: str) -> str:
        lines = content.split("\n")
        result_dict = None

        for line_num, line in enumerate(lines, 1):
            if ";" in line:
                line = line[: line.index(";")]

            line = line.strip()
            if not line:
                continue

            if line.startswith("def "):
                line = line[4:].strip()
                if " := " not in line:
                    raise SyntaxError(
                        f"Строка {line_num}: Некорректное определение константы"
                    )

                name, value_str = line.split(" := ", 1)
                name = name.strip()
                value_str = value_str.strip()

                if not re.fullmatch(r"[a-z]+", name):
                    raise SyntaxError(
                        f"Строка {line_num}: Некорректное имя константы '{name}'"
                    )

                self.constants[name] = self.parse_value(value_str)
                continue

            # Корневой словарь
            if line.startswith("{"):
                if not line.endswith("}"):
                    raise SyntaxError(
                        f"Строка {line_num}: Словарь должен быть завершен на одной строке"
                    )

                if result_dict is not None:
                    raise SyntaxError(f"Строка {line_num}: Несколько корневых словарей")

                result_dict = self.parse_dict(line[1:-1].strip())
                continue

        if result_dict is None:
            raise SyntaxError("Отсутствует корневой словарь")

        return self.dict_to_toml(result_dict)

    def dict_to_toml(self, data: Dict[str, Any], prefix: str = "") -> str:
        lines = []

        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                lines.append(f"\n[{full_key}]")
                lines.append(self.dict_to_toml(value, full_key))
            else:
                lines.append(f"{full_key} = {self.value_to_toml(value)}")

        return "\n".join(filter(None, lines))

    def value_to_toml(self, value: Any) -> str:
        if isinstance(value, int):
            return str(value)
        elif isinstance(value, list):
            elements = [self.value_to_toml(v) for v in value]
            return f"[{', '.join(elements)}]"
        elif isinstance(value, dict):
            elements = [f"{k} = {self.value_to_toml(v)}" for k, v in value.items()]
            return f"{{{', '.join(elements)}}}"
        else:
            return str(value)


def main():
    parser = argparse.ArgumentParser(
        description="Учебный конфигурационный язык с выводом в TOML"
    )
    parser.add_argument("-i", "--input", required=True, help="Путь к входному файлу")
    parser.add_argument(
        "-o", "--output", required=True, help="Путь к выходному файлу TOML"
    )

    args = parser.parse_args()

    try:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Ошибка: Файл {args.input} не найден", file=sys.stderr)
            sys.exit(1)

        with open(input_path, "r", encoding="utf-8") as f:
            input_text = f.read()

        parser = Parser()
        output_text = parser.parse_file(input_text)

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text.strip())

        print(f"Успешно преобразовано в {args.output}")

    except SyntaxError as e:
        print(f"Синтаксическая ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
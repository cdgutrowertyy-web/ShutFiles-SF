import os
import json
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "locked_files.json")
MASTER_SECRET = "SF_MASTER_SECRET_KEY_2026"
CHUNK_SIZE = 64 * 1024


def derive_key(password: str) -> bytes:
    """Превращает пароль в 32-байтный стабильный ключ через SHA-256."""
    if not password:
        seed = MASTER_SECRET
    else:
        seed = password
    return hashlib.sha256(seed.encode("utf-8")).digest()


def _xor_inplace(file_path: str, key: bytes) -> bool:
    """
    Побайтовый XOR файла "на месте" через bytearray.
    Читает файл чанками, применяет XOR с циклическим ключом и перезаписывает
    содержимое. Имя файла и расширение НЕ меняются.
    """
    try:
        key_len = len(key)
        with open(file_path, "r+b") as f:
            f.seek(0, os.SEEK_END)
            total_size = f.tell()
            f.seek(0)

            offset = 0
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                buf = bytearray(chunk)
                for i in range(len(buf)):
                    buf[i] ^= key[(offset + i) % key_len]
                f.seek(offset)
                f.write(buf)
                offset += len(buf)

                if total_size and offset >= total_size:
                    break
            f.flush()
            os.fsync(f.fileno())
        return True
    except (OSError, IOError) as e:
        print(f"[SF] Ошибка доступа к файлу {file_path}: {e}")
        return False
    except Exception as e:
        print(f"[SF] Непредвиденная ошибка при работе с {file_path}: {e}")
        return False


def crypt_file(file_path: str, password: str = "") -> bool:
    """
    Симметричное шифрование/дешифрование XOR-ом.
    Вызов дважды с одинаковым паролем возвращает исходный файл.
    """
    if not os.path.isfile(file_path):
        print(f"[SF] Файл не найден: {file_path}")
        return False
    key = derive_key(password)
    return _xor_inplace(file_path, key)


def load_database() -> list:
    """Возвращает список словарей с заблокированными файлами."""
    if not os.path.exists(DB_PATH):
        return []
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError) as e:
        print(f"[SF] Не удалось прочитать БД: {e}")
        return []


def save_database(data: list) -> bool:
    """Сохраняет список заблокированных файлов в скрытый JSON."""
    try:
        tmp_path = DB_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, DB_PATH)
        return True
    except OSError as e:
        print(f"[SF] Не удалось сохранить БД: {e}")
        return False


def add_entry(file_path: str, lock_type: str) -> bool:
    data = load_database()
    file_path = os.path.abspath(file_path)
    for entry in data:
        if os.path.abspath(entry.get("path", "")) == file_path:
            entry["type"] = lock_type
            return save_database(data)
    data.append({"path": file_path, "type": lock_type})
    return save_database(data)


def remove_entry(file_path: str) -> bool:
    data = load_database()
    file_path = os.path.abspath(file_path)
    new_data = [e for e in data if os.path.abspath(e.get("path", "")) != file_path]
    if len(new_data) == len(data):
        return False
    return save_database(new_data)


def find_entry(file_path: str):
    data = load_database()
    file_path = os.path.abspath(file_path)
    for entry in data:
        if os.path.abspath(entry.get("path", "")) == file_path:
            return entry
    return None

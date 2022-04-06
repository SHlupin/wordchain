import asyncio
import logging
from typing import List

from dawg import CompletionDAWG

from .constants import WORDLIST_SOURCE

logger = logging.getLogger(__name__)


class Words:
    # Yönlendirilmiş asiklik kelime grafiği (DAWG)
    dawg: CompletionDAWG
    count: int

    @staticmethod
    async def update() -> None:
        # Ek onaylı kelimelerle çevrimiçi repo ve veritabanı tablosundan alınan kelimeler
        logger.info("Kelimeleri alıyorum")

        async def get_words_from_source() -> List[str]:
            from . import session

            async with session.get(WORDLIST_SOURCE) as resp:
                return (await resp.text()).splitlines()

        async def get_words_from_db() -> List[str]:
            from . import pool

            async with pool.acquire() as conn:
                res = await conn.fetch("NEREDE kabul edildi kelime listesinden kelime SEÇ;")
                return [row[0] for row in res]

        source_task = asyncio.create_task(get_words_from_source())
        db_task = asyncio.create_task(get_words_from_db())
        wordlist = await source_task + await db_task

        logger.info("Kelimeleri işliyor")

        wordlist = [w.lower() for w in wordlist if w.isalpha()]
        Words.dawg = CompletionDAWG(wordlist)
        Words.count = len(Words.dawg.keys())

        logger.info("DAWG güncellendi")

from aiogram import Router
from .start import router as start_router
from .registration import router as registration_router
from .profile import router as profile_router
from .progress import router as progress_router
from .referral import router as referral_router
from .trainer import router as trainer_router
from .programs import router as programs_router
from .workout import router as workout_router
from .contact import router as contact_router
from .tips import router as tips_router
from .support import router as support_router
from .generator import router as generator_router
from .music import music_router

main_router = Router()
main_router.include_router(start_router)
main_router.include_router(registration_router)
main_router.include_router(profile_router)
main_router.include_router(progress_router)
main_router.include_router(referral_router)
main_router.include_router(trainer_router)
main_router.include_router(programs_router)
main_router.include_router(workout_router)
main_router.include_router(contact_router)
main_router.include_router(tips_router)
main_router.include_router(support_router)
main_router.include_router(generator_router)
main_router.include_router(music_router)
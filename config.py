"""Configuration for Rio Travel Search."""
import os

# RapidAPI
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '62fd3d944fmsh904551ec0b54da4p14ae54jsnbbeec1a6efb5')

# Flask
SECRET_KEY = os.getenv('SECRET_KEY', 'rio-travel-search-2026')
PORT = int(os.getenv('PORT', 5000))

# Agent info
AGENT_NAME = 'Hudson Valeriano'
AGENT_PHONE = '+14352146939'
AGENT_WHATSAPP = '+14352146939'
AGENT_EMAIL = 'contactus@riotravelpc.com'
COMPANY_NAME = 'Rio Travel LLC'
COMPANY_CITY = 'Park City, Utah'

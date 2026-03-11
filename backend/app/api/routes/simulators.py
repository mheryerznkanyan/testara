"""Simulator management routes"""
import asyncio
import json
import logging
from typing import List, Dict
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class SimulatorDevice(BaseModel):
    name: str
    udid: str
    ios_version: str
    state: str  # Booted, Shutdown


class SimulatorsResponse(BaseModel):
    devices: List[SimulatorDevice]


@router.get("/simulators", response_model=SimulatorsResponse)
async def list_simulators():
    """
    List all available iOS simulators on this machine.
    
    Returns device name, UDID, iOS version, and boot state.
    """
    try:
        # Run xcrun simctl list devices --json
        process = await asyncio.create_subprocess_exec(
            'xcrun', 'simctl', 'list', 'devices', 'available', '--json',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Failed to list simulators: {stderr.decode()}")
            return SimulatorsResponse(devices=[])
        
        data = json.loads(stdout.decode())
        devices = []
        
        # Parse devices from JSON
        for runtime, device_list in data.get('devices', {}).items():
            # Extract iOS version from runtime string
            # e.g., "com.apple.CoreSimulator.SimRuntime.iOS-26-2" → "26.2"
            ios_version = "Unknown"
            if 'iOS' in runtime:
                # Try to extract version
                parts = runtime.split('iOS-')
                if len(parts) > 1:
                    version_part = parts[1].replace('-', '.')
                    ios_version = version_part
            
            for device in device_list:
                if device.get('isAvailable'):
                    devices.append(SimulatorDevice(
                        name=device['name'],
                        udid=device['udid'],
                        ios_version=ios_version,
                        state=device['state']
                    ))
        
        logger.info(f"Found {len(devices)} available simulators")
        return SimulatorsResponse(devices=devices)
        
    except Exception as e:
        logger.error(f"Error listing simulators: {e}", exc_info=True)
        return SimulatorsResponse(devices=[])

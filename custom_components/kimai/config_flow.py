from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries


class KimaiConfigFlow(config_entries.ConfigFlow):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> None:
        if user_input is not None:
            return self.async_create_entry(title=user_input["email"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("endpoint"): str, vol.Required("email"): str, vol.Required("secret"): str}),
        )

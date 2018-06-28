import core.keystore
import expiringdict
import discord
import warnings


class None2:
	pass


SETTINGS = {
	'c-tex': {'default': True},
	'c-calc': {'default': True},
	'c-wolf': {'default': True},
	'c-roll': {'default': True},
	'f-calc-shortcut': {'default': True},
	'f-wolf-filter': {'default': False},
	'f-wolf-mention': {'default': False},
	'f-inline-tex': {'default': True},
	'f-delete-tex': {'default': False},
	'f-tex-inline': {'redirect': 'f-inline-tex', 'cannon-name': True},
	'f-tex-delete': {'redirect': 'f-delete-tex', 'cannon-name': True},
	'f-roll-unlimited': {'default': False},
	'm-disabled-cmd': {'default': True},
}


def _get_key(setting, context):
	setting = redirect(setting)
	if not isinstance(setting, str):
		raise TypeError('{} is not a valid setting'.format(setting))
	if isinstance(context, discord.Channel):
		if not context.is_private and context.id == context.server.id:
			return f'{setting}:{context.id}c'
		else:
			return f'{setting}:{context.id}'
	if isinstance(context, discord.Server):
		return f'{setting}:{context.id}'
	raise TypeError('Type {} is not a valid settings context'.format(context.__class__))


async def get_single(setting, context):
	setting = redirect(setting)
	return await core.keystore.get(_get_key(setting, context))


async def resolve(setting, *contexts, default = None2):
	if not isinstance(setting, str):
		raise TypeError('First argument of core.settings.resolve(setting, *contexts) should be a string.')
	setting = redirect(setting)
	for i in contexts:
		result = await get_single(setting, i)
		if result is not None:
			return result
	if default is not None2:
		return default
	return SETTINGS[setting]['default']


async def resolve_message(setting, message):
	setting = redirect(setting)
	if message.channel.is_private:
		so = SETTINGS[setting]
		if 'private' in so:
			return so['private']
		return so['default']
	return await resolve(setting, message.channel, message.server)


async def get_setting(message, setting):
	warnings.warn('core.settings.get_setting is deprecated', stacklevel = 2)
	return await resolve_message(setting, message)


async def set(setting, context, value):
	setting = redirect(setting)
	key = _get_key(setting, context)
	print(key, '--->', value)
	if value is None:
		await core.keystore.delete(key)
	elif value not in [0, 1]:
		raise ValueError('{} is not a valid setting value'.format(value))
	else:
		await core.keystore.set(key, value)


async def get_server_prefix(context):
	if isinstance(context, discord.message.Message):
		context = context.channel
	if isinstance(context, discord.channel.PrivateChannel):
		return '='
	if isinstance(context, discord.channel.Channel):
		if context.is_private:
			return '='
		context = context.server
	if not isinstance(context, discord.Server):
		raise TypeError('{} is not a valid server'.format(context))
	stored = await core.keystore.get('s-prefix:' + context.id)
	return '=' if stored is None else str(stored)


async def set_server_prefix(context, prefix):
	if isinstance(context, discord.Message):
		context = context.channel
	if isinstance(context, discord.Channel):
		if context.is_private:
			return '='
		context = context.server
	if not isinstance(context, discord.Server):
		raise TypeError('{} is not a valid server'.format(context))
	return (await core.keystore.set('s-prefix:' + context.id, prefix)) or '='


async def get_channel_prefix(channel):
	if channel.is_private:
		return '='
	return await get_server_prefix(channel.server)


def redirect(setting):
	if setting not in SETTINGS:
		return None
	next = SETTINGS[setting].get('redirect')
	if next:
		return redirect(next)
	return setting


def details(setting):
	return SETTINGS.get(redirect(setting))

def get_cannon_name(setting):
	if setting not in SETTINGS:
		raise KeyError(f'{setting} is not a valid setting')
	for name, details in SETTINGS.items():
		if details.get('redirect', name) == setting and details.get('cannon-name'):
			return name
	return setting

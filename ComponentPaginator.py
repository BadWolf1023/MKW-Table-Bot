import discord
from discord.ext import pages, commands
from typing import Optional

class MessagePaginator(pages.Paginator):
    def __init__(self, pages, show_disabled=True, show_indicator=False, timeout=120):
        super().__init__(pages, show_disabled=show_disabled, show_indicator=show_indicator, timeout=float(timeout))
    
    async def send(
        self,
        ctx: commands.Context,
        target: Optional[discord.abc.Messageable] = None,
        target_message: Optional[str] = None,
    ) -> discord.Message:
        """Sends a message with the paginated items.

        Parameters
        ------------
        ctx: Union[:class:`~discord.ext.commands.Context`]
            A command's invocation context.
        target: Optional[:class:`~discord.abc.Messageable`]
            A target where the paginated message should be sent, if different from the original :class:`Context`
        target_message: Optional[:class:`str`]
            An optional message shown when the paginator message is sent elsewhere.

        Returns
        --------
        :class:`~discord.Message`
            The message that was sent with the paginator.
        """
        if isinstance(ctx, discord.Message) or hasattr(ctx, 'proxy'):
            self.user = ctx.author
            ctx = ctx.channel
        elif not isinstance(ctx, commands.Context):
            raise TypeError(f"expected Context not {ctx.__class__!r}")

        if target is not None and not isinstance(target, discord.abc.Messageable):
            raise TypeError(f"expected abc.Messageable not {target.__class__!r}")

        self.update_buttons()
        page = self.pages[self.current_page]
        page = self.get_page_content(page)

        if not self.user:
            self.user = ctx.author

        if target:
            if target_message:
                await ctx.send(target_message)
            ctx = target

        self.message = await ctx.send(
            content=page if isinstance(page, str) else None,
            embeds=[] if isinstance(page, str) else page,
            view=self,
        )

        return self.message

    async def on_timeout(self) -> None:
        self.buttons.clear()
        await self.message.edit(view=None)

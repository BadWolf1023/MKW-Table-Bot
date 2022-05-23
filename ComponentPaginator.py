import discord
from discord.ext import pages, commands
from typing import Optional, Union

class MessagePaginator(pages.Paginator):
    def __init__(self, pages, show_disabled=True, show_indicator=False, timeout=120):
        super().__init__(pages, show_disabled=show_disabled, show_indicator=show_indicator, timeout=float(timeout))
    
    async def send(
        self,
        message: discord.Message,
        target: Optional[discord.abc.Messageable] = None,
        target_message: Optional[str] = None,
        reference: Optional[Union[discord.Message, discord.MessageReference, discord.PartialMessage]] = None,
        allowed_mentions: Optional[discord.AllowedMentions] = None,
        mention_author: Optional[bool] = None,
        delete_after: Optional[float] = None,
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
        reference: Optional[Union[:class:`discord.Message`, :class:`discord.MessageReference`, :class:`discord.PartialMessage`]]
            A reference to the :class:`~discord.Message` to which you are replying with the paginator. This can be created using
            :meth:`~discord.Message.to_reference` or passed directly as a :class:`~discord.Message`. You can control
            whether this mentions the author of the referenced message using the :attr:`~discord.AllowedMentions.replied_user`
            attribute of ``allowed_mentions`` or by setting ``mention_author``.
        allowed_mentions: Optional[:class:`~discord.AllowedMentions`]
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.
        mention_author: Optional[:class:`bool`]
            If set, overrides the :attr:`~discord.AllowedMentions.replied_user` attribute of ``allowed_mentions``.
        delete_after: Optional[:class:`float`]
            If set, deletes the paginator after the specified time.

        Returns
        --------
        :class:`~discord.Message`
            The message that was sent with the paginator.
        """
        if not hasattr(message, 'proxy') and not isinstance(message, discord.Message):
            raise TypeError(f"expected Message not {message.__class__!r}")

        if target is not None and not isinstance(target, discord.abc.Messageable):
            raise TypeError(f"expected abc.Messageable not {target.__class__!r}")

        if reference is not None and not isinstance(
            reference, (discord.Message, discord.MessageReference, discord.PartialMessage)
        ):
            raise TypeError(f"expected Message, MessageReference, or PartialMessage not {reference.__class__!r}")

        if allowed_mentions is not None and not isinstance(allowed_mentions, discord.AllowedMentions):
            raise TypeError(f"expected AllowedMentions not {allowed_mentions.__class__!r}")

        if mention_author is not None and not isinstance(mention_author, bool):
            raise TypeError(f"expected bool not {mention_author.__class__!r}")

        self.update_buttons()
        page = self.pages[self.current_page]
        page_content = self.get_page_content(page)

        self.user = message.author
        messageable = message.channel

        if page_content.custom_view:
            self.update_custom_view(page_content.custom_view)

        if target:
            if target_message:
                await messageable.send(
                    target_message,
                    reference=reference,
                    allowed_mentions=allowed_mentions,
                    mention_author=mention_author,
                )
            messageable = target

        self.message = await messageable.send(
            content=page_content.content,
            embeds=page_content.embeds,
            files=page_content.files,
            view=self,
            reference=reference,
            allowed_mentions=allowed_mentions,
            mention_author=mention_author,
            delete_after=delete_after,
        )

        return self.message


    async def on_timeout(self) -> None:
        self.buttons.clear()
        await self.message.edit(view=None)

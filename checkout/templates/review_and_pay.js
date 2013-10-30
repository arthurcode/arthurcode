var form_div = Y.one('div.add-gift-card');
if (form_div && form_div.hasClass('hidden')) {
    // give the user a way to toggle form visibility
    var node = Y.Node.create('<span class="toggle-gift-card subtle">{% if gift_cards %}redeem another gift card{% else %}redeem a gift card{% endif %}</span>');
    node.on("click", function(e) {
        form_div.toggleClass('hidden');
    });
    form_div.ancestor().prepend(node);
}

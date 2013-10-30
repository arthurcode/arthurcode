// roll up long lists of filters
var to_roll = Y.all('ul.roll');
var max_allowed = 4;

function roll(ul) {
    var items = ul.all('li');
    if (items.size() > max_allowed + 1) {
        // roll it up!
        var to_hide = items.slice(max_allowed);
        to_hide.each(function(li) {
            li.addClass('hidden');
        });
        var trigger = Y.Node.create('<li class="roll-trigger"><a href="">more choices <span class="count">(' + to_hide.size() + ')</span></a></li>');
        ul.appendChild(trigger);
        trigger.on('click', function(e) {
            e.preventDefault();
            ul.removeChild(trigger);
            unroll(ul);
        });
    }
}

function unroll(ul) {
    ul.all('li').each(function(li) {
        li.removeClass('hidden');
    });
    var trigger = Y.Node.create('<li class="roll-trigger"><a href="">fewer choices</a></li>');
    ul.appendChild(trigger);
    trigger.on('click', function(e) {
        e.preventDefault();
        ul.removeChild(trigger);
        roll(ul);
    });
}

to_roll.each(function(ul) {
    roll(ul);
});

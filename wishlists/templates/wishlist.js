/**
 * Created with PyCharm.
 * User: rhyanarthur
 * Date: 2013-10-30
 * Time: 11:53 AM
 * To change this template use File | Settings | File Templates.
 */

Y.all('div.note-form').each(function(div) {
    if (div.hasClass('bound')) {
        return;
    }
    // the form section is unbound, and should be hidden.
    var cell = div.ancestor('td');
    var note = div.one('textarea#id_note');

    if (cell && note) {
        div.addClass('hidden');
        var noteSpan = Y.Node.create('<span class="note">' + note.getHTML() + '</span>');
        cell.appendChild(noteSpan);
        var toggleText = '';
        if (note.getHTML()) {
            toggleText = 'edit';
        } else {
            toggleText = 'add a note';
        }
        var toggle = Y.Node.create('<a class="toggle subtle" href="">' + toggleText + '</a>');
        cell.appendChild(toggle);

        toggle.on('click', function(e) {
            e.preventDefault();
            noteSpan.toggleClass('hidden');
            div.toggleClass('hidden');
            if (noteSpan.hasClass('hidden')) {
                toggle.setHTML('cancel');
            } else {
                toggle.setHTML(toggleText);
            }
        });
    }
});

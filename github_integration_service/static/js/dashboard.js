$(document).ready(function () {
  // View Diff Modal
  $(document).on('click', '.view-diff', function () {
    const repo = $(this).data('repo');
    $('#modalRepoName').text(repo);
    $('.accept-push, .open-pr').data('repo', repo);
    $('#diffContent').html('<div class="text-center py-5">Loading…</div>');

    $.get(`/api/diff/${encodeURIComponent(repo)}`, function (html) {
      $('#diffContent').html(html);
    }).fail(function () {
      $('#diffContent').html('<div class="alert alert-danger">Failed to load diff.</div>');
    });
  });

  // Toggle Active
  $(document).on('change', '.toggle-active', function () {
    const repo = $(this).closest('tr').data('repo');
    const isActive = $(this).is(':checked');

    $.post('/api/toggle-active', { repo, is_active: isActive })
      .fail(() => alert('Failed to update state.'));
  });

  // Regenerate
  $(document).on('click', '.regenerate', function () {
    const repo = $(this).data('repo');
    $.post('/api/regenerate', { repo })
      .done(() => alert('Regeneration started.'))
      .fail(() => alert('Failed to start regeneration.'));
  });




  // Delete Repo
  $(document).on('click', '.delete-repo', function () {
    const repo = $(this).data('repo');
    if (!confirm(`Are you sure you want to delete the repository "${repo}"?`)) return;

    $.ajax({
      url: `http://localhost:8000/api/delete-repo`,
      method: 'POST',
      data: { repo },
      success: () => {
        $(`tr[data-repo="${repo}"]`).remove();
        console.log("rishabh");
        alert(`Repository "${repo}" deleted.`);
      },
      error: () => alert('Failed to delete repository.')
    });
  });
});

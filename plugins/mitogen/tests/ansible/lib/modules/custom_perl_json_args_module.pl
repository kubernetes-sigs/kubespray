#!/usr/bin/perl

binmode STDOUT, ":utf8";
use utf8;

use JSON;

my $json_args = <<'END_MESSAGE';
<<INCLUDE_ANSIBLE_MODULE_JSON_ARGS>>
END_MESSAGE

print encode_json({
    message => "I am a perl script! Here is my input.",
    input => [decode_json($json_args)]
});

#!/usr/bin/perl

binmode STDOUT, ":utf8";
use utf8;

my $WANT_JSON = 1;

use JSON;

my $json;
{
  local $/; #Enable 'slurp' mode
  open my $fh, "<", $ARGV[0];
  $json_args = <$fh>;
  close $fh;
}

print encode_json({
    message => "I am a want JSON perl script! Here is my input.",
    input => [decode_json($json_args)]
});

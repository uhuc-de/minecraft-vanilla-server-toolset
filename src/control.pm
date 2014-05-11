#!/usr/bin/perl

use strict;
use warnings;
use utf8;

package control;

use YAML ();
use Getopt::Long;

use IO::Socket;

use v5.10.1;

sub new
	{
		my $class = 'control';
		my $self = bless(
										 {
											'config' => {}
										 },
										 $class
										);
		$self->configure();
		$self->connect_socket() if ($self->{'config'}->{'autoconnect'});

		return $self;
	}

sub connect_socket
	{
		my $self = shift;

		$_ = $self->{'config'}->{'server'}->{'port'}->[0];
		if (m|^(?<filename>.*?) \s+ / \s+ UNIX$|x) {
			$self->{'socket'} = IO::Socket::UNIX->new(
																								Peer     => $+{'filename'},
																								Type     => SOCK_STREAM
																							 );
		} elsif (m|^\d+$| && $self->{'config'}->{'server'}->{'host'} && $self->{'config'}->{'server'}->{'proto'}) {
			$self->{'socket'} = IO::Socket::INET->new(
																								PeerAddr => $self->{'config'}->{'server'}->{'host'},
																								PeerPort => $_,
																								Proto    => $self->{'config'}->{'server'}->{'proto'}
																							 );
		} else {
			die("Socket type not implemented at this time (Port spec: $_)");
		}
		unless ($self->{'socket'})
			{
				die("Failed to connect to socket (Port spec: ".$self->{'config'}->{'server'}->{'port'}->[0]."): $@");
			}
	}

sub say
	{
		my $self = shift;

		print { $self->{'socket'} } (@_, "\r\n")
			or die("Could not print message to socket");
	}

sub get
	{
		my $self = shift;

		my $line = $self->{'socket'}->getline();
		return undef unless (defined($line));
		$line =~ s/\r?\n$//;
		$line =~ s|^[\d\-]+ [\d:]+ \[.*?\] ||;

		return $line;
	}

sub main
	{
		my $self = __PACKAGE__->new();

		use IO::Interactive qw(is_interactive);

		if ((! $self->{'config'}->{'force_raw'}) && ($self->{'config'}->{'force_shell'} || is_interactive()))
			{
				$self->_shell();
			}
		else
			{
				$self->_listen();
			}
	}

sub _listen
	{
		my $self = shift;

		my $ok = eval
			{
				require IO::Select;
				require sigtrap;
				sigtrap->import('untrapped', 'handler', sub { exit 0; });
			};
		unless ($ok)
			{
				print STDERR "Failed to include necessary modules\n".$@."\n";
				exit 1;
			}

		my $select = IO::Select->new();
		$select->add(\*STDIN);
		$select->add($self->{'socket'});

		while (my @ready = $select->can_read())
			{
				foreach my $fh (@ready)
					{
						my $bytes;
						my $bytes_read;

						if (! ( $bytes_read = $fh->sysread($bytes, 4096) ) && $fh == $self->{'socket'})
							{
								die("Remote end hung up");
							}

						if ($fh == $self->{'socket'})
							{
								$bytes =~ s/\r\n/\n/sg;
								print $bytes;
							}
						else
							{
								$bytes =~ s/\n/\r\n/sg;
								print { $self->{'socket'} } $bytes;

								exit 0 if (eof($fh) && ! $self->{'config'}->{'keep_alive'});
							}
					}
			}
	}

sub _shell
	{
		my $self = shift;

		our $more = 1;

		my $ok = eval
			{
				require Curses;
				Curses->import();
				require Term::ReadKey;
				Term::ReadKey->import();
				require IO::Select;
				require sigtrap;
				sigtrap->import('handler', sub {},  'normal-signals', 'handler', sub { $more = 0; }, 'INT');
			};
		unless ($ok)
			{
				print STDERR "Failed to include necessary modules\n".$@."\n";
				exit 1;
			}

		my @lines = ();
		my $input = '';
		my $select = IO::Select->new();
		my $info = 'Use ^C or ^D to exit';
		my $info_set = 0;

		my $msg = '';

		$select->add(\*STDIN);
		$select->add($self->{'socket'});

		my $old_stderr = fileno(*STDERR);
		open(STDERR, '>&'.fileno(*STDIN));

		initscr();
		ReadMode('cbreak');
		clear();

		start_color() if (has_colors());

		use_default_colors();
		init_pair(1, 6, -1);
		init_pair(2, 3, -1);

		main: while ($more)
			{
				clear();

				my ($width, $height) = GetTerminalSize();
				my @print = ( (['', 0, 0, 1, 0]) x $height, @lines )[2 - $height .. -1];
				my $info_str = '';
				$info_str = '-( '.substr($info, 0, $width - 6).' )-' if ($info && $info ne '');
				push(@print, [$info_str.'-' x ($width - length($info_str)), 0, 0, 1, 0]);
				push(@print, [substr($input, ( - ($width - 2) )), ( length($input) > ($width - 2) ) ? 1 : 0, 0, 1, 0]);

				my $row = 0;
				for(@print)
					{
						my ($str, $pre, $post, $terminates, $recv) = @{$_};
						my $p = 1;
						$p = 0 if ($row == $height - 2);
						if ($pre && $p)
							{
								attron(COLOR_PAIR(1));
								addstr($row, 0, '%');
								attroff(COLOR_PAIR(1));
							}
						elsif (! $p)
							{
								addstr($row, 0, ' ');
							}
						if ($recv)
							{
								attron(COLOR_PAIR(2));
							}
						addstr($row, $p ? 1 : 0, $str);
						if ($recv)
							{
								attroff(COLOR_PAIR(2));
							}
						if ($post && $p)
							{
								clrtoeol();
								attron(COLOR_PAIR(1));
								addstr($row, ($width - 1), '%');
								attroff(COLOR_PAIR(1));
							}
						clrtoeol();
						$row++;
					}
				refresh();

				if (my @ready = $select->can_read())
					{
						foreach my $fh (@ready)
							{
								my $bytes;
								my $bytes_read;
								unless ($bytes_read = $fh->sysread($bytes, 4096))
									{
										$msg = 'One end hung up.';
										last main;
									}

								if ($fh == $self->{'socket'})
									{
										my $terminates = 0;
										$terminates = 1 if ($bytes =~ m/\r?\n$/s);
										my @read_lines = split(/\r?\n/, $bytes);

										my ($ref, $count) = _linewrap(\@lines, \@read_lines, $width, $terminates, 1);
										@lines = @{$ref};

										$info = "Received ${count} lines";
									}
								else
									{
										if (! $info_set)
											{
												$info = '';
											}

										$input .= $bytes;

										given ($input)
											{
												when (m/(?<input>.*)[\r\n]$/)
													{
														$self->say($+{'input'});

														my ($ref, $count) = _linewrap(\@lines, [$+{'input'}], $width, 1, 0);
														@lines = @{$ref};

														$info = "Sent ${count} lines";

														$input = '';
													}
												when (m/[\cC\cD]/)
													{
														last main;
													}
												when (m/.?\177|[^ -~]/)
													{
														$input =~ s/.?\177|[^ -~]//;
													}
											}
									}
							}
					}
			}

		ReadMode('restore');
		endwin();

		open(STDERR, '>&'.$old_stderr);

		print STDERR $msg."\n" if ($msg ne '');

		exit 0;
	}

sub _linewrap
	{
		my @target = @{shift()};
		my @source = @{shift()};
		my $width = shift();
		my $terminated = shift();
		my $recv = shift();
		my $count = 0;

		foreach my $line (@source) {
			my @last = ('', 0, 0, 1, 0);
			@last = @{$target[-1]} if (exists($target[-1]) && defined($target[-1]) && ref($target[-1]) eq "ARRAY");
			if (! $last[3] && $last[4] && $recv)
				{
					$target[-1]->[0] .= $line;
					$target[-1]->[3] = 1;
				}
			elsif (! $last[3] && ! $last[4] && $recv)
				{
					push(@target, [$line, 1, 0, 1, $recv]);
				}
			else
				{
					if (! $last[3])
						{
							$target[-1]->[2] = 1;
							$target[-1]->[3] = 1;
						}
					push(@target, [$line, 0, 0, 1, $recv]);
				}

			while (length($target[-1]->[0]) > ($width - 2)) {
				my $old = $target[-1]->[0];
				$target[-1] = [substr($old, 0, ($width - 2)), $target[-1]->[1], 1, 1, $recv];
				push(@target, [substr($old, ($width - 2)), 1, 0, 1, $recv]);
			}
			$count++;
		}

		$target[-1]->[3] = $terminated;

		return \@target, $count;
	}

sub configure
	{
		my $self = shift;

		my $c;

		# Read default config
		($c) = YAML::LoadFile(\*control::DATA);
		_deepmerge_hashes($c, $self->{'config'});

		# Read commandline arguments
		$c = {};
		GetOptions(
							 $c,
							 'config|c=s%',
							 'autoconnect|a!',
							 'force-shell|shell|s!',
							 'force-raw|raw|r!',
							 'keep-alive|persist|k|p!',
							 'verbose|v+'
							);
		while (my ($key, $value) = each(%{$c})) {
			my $new_key = $key;
			$new_key =~ s/\-/_/g;
			unless ($key eq $new_key)
				{
					$c->{$new_key} = $value;
					delete($c->{$key});
				}
		}
		_deepmerge_hashes($c, $self->{'config'});

		# Read config file
		$self->_read_config();
	}

# Read config file
sub _read_config
	{
		my $self = shift;

		my $ok;
		my $c;

		$ok = eval
			{
				($c) = YAML::LoadFile($self->{'config'}->{'config'}->{'self'});
			};
		if ($ok)
			{
				# Merge read config into default
				_deepmerge_hashes($c, $self->{'config'});
			}
		else
			{
				warn($@) if ($self->{'config'}->{'verbose'} > 0);
			}

		$ok = eval
			{
				($c) = YAML::LoadFile($self->{'config'}->{'config'}->{'instance'});
			};
		if ($ok)
			{
				# Merge parts of read config
				my @whitelist = ('server');
				while (my ($key, $value) = each(%{$c}))
					{
						my $valid = 0;
						foreach my $test (@whitelist)
							{
								next unless ($test eq $key);
								$valid = 1;
								last;
							}
						next if ($valid);
						delete($c->{$key});
					}
				_deepmerge_hashes($c, $self->{'config'});
			}
		else
			{
				warn($@) if ($self->{'config'}->{'verbose'} > 0);
			}
	}

# Recursively merge to hashes
sub _deepmerge_hashes
	{
		my ($source, $target) = @_;

		while (my($key, $value) = each (%{$source}))
			{
				if (ref($value) eq "HASH")
					{
						unless (ref($target->{$key}) eq "HASH")
							{
								$target->{$key} = {};
							}
						_deepmerge_hashes($value, $target->{$key});
					}
				else
					{
						$target->{$key} = $value;
					}
			}
	}

__PACKAGE__->main() unless caller;

return 1;
__DATA__
config:
  self: 'config.yaml'
  instance: 'config.yaml'
server:
  proto: 'tcp'
  host: '127.0.0.1'
  port:
    - '/tmp/mcwrapper.socket / UNIX'
  ipv: 4
autoconnect: 1
force_shell: 0
force_raw: 0
verbose: 0
keep_alive: 0

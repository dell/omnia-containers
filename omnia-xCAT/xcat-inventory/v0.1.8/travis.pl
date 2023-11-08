# IBM(c) 2007 EPL license http://www.eclipse.org/legal/epl-v10.html

use strict;
use warnings;
use Getopt::Long;
use Data::Dumper;
use Time::Local;
use File::Basename;
use File::Path;
use File::Find;
use Encode;
use Encode::CN;
use JSON;
use URI::Escape;
use LWP::Simple;

#---Global attributes---
my $rst = 0;
my $retries = 5; # Try this many times to get response
my $check_result_str="``CI CHECK RESULT`` : ";
my $last_func_start = timelocal(localtime());
my $GITHUB_API = "https://api.github.com";

my $inventory_pkg = "";

use Term::ANSIColor qw(:constants);
$Term::ANSIColor::AUTORESET = 1;

runcmd("sudo rm -rf /bin/sh");
runcmd("sudo ln -s /bin/bash /bin/sh");

#--------------------------------------------------------
# Fuction name: runcmd
# Description:  run a command after 'cmd' label in one case
# Attributes:
# Return code:
#      $::RUNCMD_RC : the return code of command
#      @$outref  : the output of command
#--------------------------------------------------------
sub runcmd
{
    my ($cmd) = @_;
    my $rc = 0;
    $::RUNCMD_RC = 0;
    my $outref = [];
    @$outref = `$cmd 2>&1`;
    if ($?)
    {
        $rc          = $?;
        $rc          = $rc >> 8;
        $::RUNCMD_RC = $rc;
    }
    chomp(@$outref);
    return @$outref;
}

sub send_back_comment{
    my $message = shift;

    my $comment_url = "$GITHUB_API/repos/$ENV{'TRAVIS_REPO_SLUG'}/issues/$ENV{'TRAVIS_PULL_REQUEST'}/comments";
    my $json = new JSON;
    my $comment_len = 0;
    my $comment_content;
    my $comment_url_resp;
    my $counter = 1;
    while($counter <= $retries) {
        $comment_url_resp = get($comment_url);
        if ($comment_url_resp) {
            last; # Got response, no more retries
        } else {
            sleep($counter*2); # Sleep and try again
            print "[send_back_comment] $counter Did not get response, sleeping ". $counter*2 . "\n";
            $counter++;
        }
    }
     unless ($comment_url_resp) {
        print "[send_back_comment] After $retries retries, not able to get response from $comment_url \n";
        # Failed after trying a few times, return
        return;
    }
    print "\n\n>>>>>Dumper comment_url_resp:\n";
    print Dumper $comment_url_resp;

    $comment_content = $json->decode($comment_url_resp);
    $comment_len = @$comment_content;

    my $post_url = $comment_url;
    my $post_method = "POST";
    if($comment_len > 0){
        foreach my $comment (@{$comment_content}){
            if($comment->{'body'} =~ /CI CHECK RESULT/) {
                 $post_url = $comment->{'url'};
                 $post_method = "PATCH";
            }
        }
    }

     print "[send_back_comment] method = $post_method to $post_url\n";
     `curl -u "$ENV{'xcatbotuser'}:$ENV{'xcatbotpw'}" -X $post_method -d '{"body":"$message"}' $post_url`;
}

sub build_xcat_inventory{
    my @output;
    my $cmd = "sudo ./build.sh";
    @output = runcmd("$cmd");
    print ">>>>>Dumper the output of '$cmd'\n";
    #print Dumper \@output;
    if($::RUNCMD_RC){
        print "[build_xcat_inventory] $cmd ....[Failed]\n";
        #print Dumper \@output;
        #$check_result_str .= "> **BUILD ERROR**, Please click ``Details`` label in ``Merge pull request`` box for detailed information";
        #send_back_comment("$check_result_str");
        return 1;
    } else {
        print "[build_xcat_inventory] $cmd ....[Pass]\n";
        if ($output[-1] =~ /Package path is (.*)/) {
            $inventory_pkg = $1;
        }
        #$check_result_str .= "> **BUILD SUCCESSFUL** ";
        #send_back_comment("$check_result_str");
    }
    return 0;
}

sub install_xcat {
    my @cmds = ("sudo mkdir -p /xcat && cd /xcat",
               "sudo wget -q https://xcat.org/files/xcat/xcat-core/devel/Ubuntu/core-snap/core-debs-snap.tar.bz2",
               "sudo tar -jxvf core-debs-snap.tar.bz2",
               "cd xcat-core && sudo ./mklocalrepo.sh",
               "sudo chmod 777 /etc/apt/sources.list",
               "sudo echo \"deb [arch=amd64 allow-insecure=yes] http://xcat.org/files/xcat/repos/apt/devel/xcat-dep xenial main\" >> /etc/apt/sources.list",
               "sudo echo \"deb [arch=ppc64el allow-insecure=yes] http://xcat.org/files/xcat/repos/apt/devel/xcat-dep xenial main\" >> /etc/apt/sources.list",
               "sudo wget -q -O - \"http://xcat.org/files/xcat/repos/apt/apt.key\" | sudo apt-key add -",
               "sudo apt-get -qq update");
    my @output;
    foreach my $cmd (@cmds){
        print "[install_xcat] running $cmd\n";
        @output = runcmd("$cmd");
        if ($::RUNCMD_RC){
            print RED "[install_xcat] $cmd. ...[Failed]\n";
            print "[install_xcat] error message:\n";
            #print Dumper \@output;
            #$check_result_str .= "> **INSTALL XCAT ERROR** : Please click ``Details`` label in ``Merge pull request`` box for detailed information ";
            #send_back_comment("$check_result_str");
            return 1;
        }
    }

    my $cmd = "sudo apt-get install xcat --allow-remove-essential --allow-unauthenticated";
    @output = runcmd("$cmd");
    if($::RUNCMD_RC){
        my $lastline = $output[-1];
        $lastline =~ s/[\r\n\t\\"']*//g;
        print "[install_xcat] $cmd ....[Failed]\n";
        print ">>>>>Dumper the output of '$cmd'\n";
        #print Dumper \@output;
        #$check_result_str .= "> **INSTALL XCAT ERROR** : Please click ``Details`` label in ``Merge pull request`` box for detailed information";
        #send_back_comment("$check_result_str");
        return 1;
    }else{
        print "[install_xcat] $cmd ....[Pass]\n";
    }

    my $sshcmd = "sudo bash -c 'echo StrictHostKeyChecking no >> ~root/.ssh/config && echo UserKnownHostsFile /dev/null >> ~root/.ssh/config && cat ~root/.ssh/id_rsa.pub >> ~root/.ssh/authorized_keys'";
    @output = runcmd("$sshcmd");
    if ($::RUNCMD_RC){
        print RED "[install_xcat] $sshcmd. ...[Failed]\n";
        print Dumper \@output;
        return 1;
    }

    return 0;
}

sub install_xcattest {
    my $cmd = "sudo apt-get install xcat-test --allow-remove-essential --allow-unauthenticated";
    my @output = runcmd("$cmd");
    if($::RUNCMD_RC){
         print RED "[install_xcattest] $cmd ....[Failed]\n";
         print Dumper \@output;
         return 1;
    }else{
        print "[install_xcattest] $cmd .....:\n";
        #print Dumper \@output;
    }

    # get newest xcat-inventory cases from github and update
    my $gitdir = "/tmp/xcat-core";
    mkdir($gitdir);
    $cmd = "sudo git clone https://github.com/xcat2/xcat-core.git $gitdir";
    @output = runcmd("$cmd");
    if($::RUNCMD_RC){
        print RED "[install_xcattest] $cmd ....[Warning]\n";
        print Dumper \@output;
    }else{
        print "[install_xcattest] $cmd .....:\n";
        $cmd = "sudo cp -f $gitdir/xCAT-test/xcattest /opt/xcat/bin/xcattest";
        @output = runcmd("$cmd");
        if ($::RUNCMD_RC){
            print RED "[install_xcattest] $cmd ....[Warning]\n";
            print Dumper \@output;
        }
        $cmd = "sudo cp -Rrf $gitdir/xCAT-test/autotest/testcase/xcat_inventory/* /opt/xcat/share/xcat/tools/autotest/testcase/xcat_inventory";
        @output = runcmd("$cmd");
        if ($::RUNCMD_RC){
            print RED "[install_xcattest] $cmd ....[Warning]\n";
            print Dumper \@output;
        }
    }

    $cmd = "sudo bash -c '. /etc/profile.d/xcat.sh && xcattest -h'";
    @output = runcmd("$cmd");
    if($::RUNCMD_RC){
         print RED "[install_xcattest] $cmd ....[Failed]\n";
         print "[install_xcattest] error dumper:\n";
         print Dumper \@output;
         return 1;
    }else{
         print "[install_xcattest] $cmd .....:\n";
    }
    return 0;
}

sub install_inventory {
    my $cmd = "sudo apt-get install -y $inventory_pkg";
    my @output = runcmd("$cmd");
    if ($::RUNCMD_RC){
        print "[install_inventory] $cmd ....[Failed]\n";
        print ">>>>>Dumper the output of '$cmd'\n";
        print Dumper \@output;
        #$check_result_str .= "> **INSTALL XCAT ERROR** : Please click ``Details`` label in ``Merge pull request`` box for detailed information";
        #send_back_comment("$check_result_str");
        return 1;
    } else {
        print "[install_inventory] $cmd ....[Pass]\n"; 
    }
    return 0;
}

sub run_inventory_cases {
    my $hostname = `hostname`;
    chomp($hostname);
    print "hostname = $hostname\n";
    my $conf_file = "$ENV{'PWD'}/inventory.conf";
    my $dstip = `hostname -i | cut -d" " -f1`;
    chomp($dstip);
    my $cmd = "echo '[System]' > $conf_file; echo 'MN=$hostname' >> $conf_file; echo 'DSTMN'=$dstip >> $conf_file; echo '[Table_site]' >> $conf_file; echo 'key=domain' >>$conf_file; echo 'value=pok.stglabs.ibm.com' >> $conf_file";
    my @output = runcmd("$cmd");
    if($::RUNCMD_RC){
         print RED "[run_inventory_cases] $cmd ....[Failed]";
         print "[run_inventory_cases] error dumper:\n";
         print Dumper \@output;
         return 1;
    }

    print "Dumper regression conf file:\n";
    @output = runcmd("cat $conf_file");
    print Dumper \@output;

    $cmd = "sudo bash -c '. /etc/profile.d/xcat.sh && xcattest -s \"inventory_ci\" -l'";
    my @caseslist = runcmd("$cmd");
    if($::RUNCMD_RC){
         print RED "[run_inventory_cases] $cmd ....[Failed]\n";
         print "[run_inventory_cases] error dumper:\n";
         print Dumper \@caseslist;
         return 1;
    }else{
         print "[run_inventory_cases] $cmd .....:\n";
         print Dumper \@caseslist;
    }

    my $casenum = @caseslist;
    my $x = 0;
    my @failcase;
    my $passnum = 0;
    my $failnum = 0;
    foreach my $case (@caseslist){
        ++$x;
        $cmd = "sudo bash -c '. /etc/profile.d/xcat.sh &&  xcattest -f $conf_file -t $case'";
        print "[run_inventory_cases] run $x: $cmd\n";
        @output = runcmd("$cmd");
        for(my $i = $#output; $i>-1; --$i){
            if($output[$i] =~ /------END::(.+)::Failed/){
                push @failcase, $1;
                ++$failnum;
                print Dumper \@output;
                last;
             }elsif ($output[$i] =~ /------END::(.+)::Passed/){
                ++$passnum;
                #print "[run_inventory_cases] $1 ------------------ Passed\n";
                last;
             }
         }
    }

    if($failnum){
        my $log_str = join (",", @failcase );
        print "**INVENTORY TEST Failed**: Totalcase $casenum Passed $passnum Failed $failnum FailedCases: $log_str.";
        #$check_result_str .= "> **INVENTORY TEST Failed**: Totalcase $casenum Passed $passnum Failed $failnum FailedCases: $log_str.  Please click ``Details`` label in ``Merge pull request`` box for detailed information";
        #send_back_comment("$check_result_str");
        return 1;
    }else{
        #$check_result_str .= "> **INVENTORY  TEST Successful**: Totalcase $casenum Passed $passnum Failed $failnum";
        #send_back_comment("$check_result_str");
    }

    return 0;
}

sub mark_time{
    my $func_name=shift;
    my $nowtime    = timelocal(localtime());
    my $nowtime_str = scalar(localtime());
    my $duration = $nowtime - $last_func_start;
    $last_func_start = $nowtime;
    print "[mark_time] $nowtime_str, ElapsedTime of $func_name is $duration s\n";
}

#===============Main Process=============================
print GREEN "\n------ Travis Environment Attributes ------\n";
my @travis_env_attr = ("TRAVIS_REPO_SLUG",
                       "TRAVIS_BRANCH",
                       "TRAVIS_EVENT_TYPE",
                       "TRAVIS_PULL_REQUEST",
                       "GITHUB_TOKEN",
                       "USERNAME",
                       "PASSWORD",
                       "PWD");
foreach (@travis_env_attr){
    if($ENV{$_}) {
        print "$_ = '$ENV{$_}'\n";
    } else {
        print "$_ = ''\n";
    }
}

my @os_info = runcmd("cat /etc/os-release");
print "Current OS information:\n";
print Dumper \@os_info;

my @disk = runcmd("df -h");
print "Disk information:\n";
print Dumper \@disk;

my @intfinfo = runcmd("ip -o link |grep 'link/ether'|grep 'state UP' |awk -F ':' '{print \$2}'|head -1");
foreach my $nic (@intfinfo) {
    print "Hacking the netmask length to 16 if it is 32: $nic\n";
    runcmd("ip -4 addr show $nic|grep 'inet'|grep -q '/32' && sudo ip addr add \$(hostname -I|awk '{print \$1}')/16 dev $nic");
}
my @ipinfo = runcmd("ip addr");
print "Networking information:\n";
print Dumper \@ipinfo;

#Start to build xcat-inventory
print  GREEN "\n------ Building xCAT inventory package ------\n";
$rst = build_xcat_inventory();
if($rst){
    print RED "Build of xCAT inventory package failed\n";
    exit $rst;
}
mark_time("build_xcat_inventory");

# Start to install xcat
print GREEN "\n------Installing xCAT ------\n";
$rst = install_xcat();
if($rst){
    print RED "Install of xCAT failed\n";
    exit $rst;
}
mark_time("install_xcat");

# Start to install xcat-test
print GREEN "\n------Installing xCAT test------\n";
$rst = install_xcattest();
if($rst){
    print RED "Install of xCAT test failed\n";
    exit $rst;
}
mark_time("install_xcattest");

# Start to install xcat-inventory
print GREEN "\n------Installing xcat-inventory------\n";
$rst = install_inventory();
if($rst){
    print RED "Install of xcat-inventory failed\n";
    exit $rst;
}
mark_time("install_inventory");

# Start to run xcat-inventory cases
print GREEN "\n------Running xcat-inventory CI cases------\n";
$rst = run_inventory_cases();
if($rst){
    print RED "Run xcat-inventory testcases failed\n";
    exit $rst;
}
mark_time("run_inventory_cases");

exit 0;

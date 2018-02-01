#!/usr/bin/ruby

require 'json'
require 'optparse'
require 'ostruct'

AWS_TEMPLATE_FORMAT_VERSION = '2010-09-09'
IMAGE_ID = 'ami-b97a12ce'
INSTANCES = 1
INSTANCE_TYPE = 't2.micro'
ALLOW_SSH_FROM = ''

def outputs_block(public_ip)
  {'PublicIP' => public_ip.jsonify}
end

def resources_block(instances, security_group)
  result = {}
  instances.each do |x|
    result[x.name] = x.properties
  end
  result['InstanceSecurityGroup'] = security_group.jsonify
  return result
end

def format_output(public_ip, instances, security_group)
  # Convert the provided arguments into a single hash that JSON understands.
  result = {}
  result['AWSTemplateFormatVersion'] = AWS_TEMPLATE_FORMAT_VERSION
  result['Outputs'] = outputs_block(public_ip)
  result['Resources'] = resources_block(instances, security_group)
  return result
end

def create_ingress_rule(allow_ssh_from)
  ingress_rule = IngressRule.new
  # I'm unsure about how to dynamically generate a subnet from the
  # information provided so I decided this method was necessary.
  if allow_ssh_from != ''
    ingress_rule.cidr_ip = allow_ssh_from + '/32'
  end
  return ingress_rule
end

def create_security_group(ingress_rule)
  security_group = InstanceSecurityGroup.new(
    'Enable SSH access via port 22',
    ingress_rule
    )
  return security_group
end

def create_instance(instance_type, security_group)
  instance = EC2Instance.new(instance_type = instance_type, security_group)
  return instance
end


class PublicIP
  @@description = 'Public IP address of the newly created EC2 instance'
	
  attr_accessor :value
	
  def initialize
    @value = {'Fn::GetAtt' => ['EC2Instance', 'PublicIp']}
  end
	
  def jsonify
    {'Description' => @@description, 'Value' => @value}
  end
end


class EC2Instance
  # Defines an EC2 instance
  # Params:
  # +instance_type+:: the instance type of the EC2 instance
  # (e.g. 't2.micro', 't2.small', etc.)
  # +security_groups+:: the security groups to which this instance belongs
  # takes any number of +InstanceSecurityGroup+ objects

  @@num = 0
	
  attr_accessor :name, :image_id, :instance_type, :security_groups, :type
	
  def initialize(instance_type = INSTANCE_TYPE, *security_groups)
    @@num += 1
    @name = getName
    @image_id = IMAGE_ID
    @instance_type = instance_type
    @security_groups = security_groups
    @type = 'AWS::EC2::Instance'
  end
	
  def properties
    security_groups = []
    @security_groups.each do |x|
      security_groups << {'Ref' => x.class.name}
    end
		
    result = {
      'ImageId' => @image_id,
      'InstanceType' => @instance_type,
      'SecurityGroups' => security_groups
    }
    {'Properties' => result, 'Type' => @type}
  end
  
  private
  
  def getName
    default = 'EC2Instance'
    if @@num > 1
      return "#{default}#{@@num}"
    end
    return default
  end
end


class InstanceSecurityGroup
  attr_accessor :description, :security_group_ingress, :type
	
  def initialize(description = '', *rules)
    @description = description
    @security_group_ingress = rules
    @type = 'AWS::EC2::SecurityGroup'
  end
	
  def jsonify
    security_rules = []
    @security_group_ingress.each do |x|
      security_rules << x.jsonify
    end
    properties = {
      'GroupDescription' => @description,
      'SecurityGroupIngress' => security_rules
      }
    result = {'Properties' => properties, 'Type' => @type}
  end
	
  def addIngressRule(rule)
    @security_group_ingress << rule
  end
end


class IngressRule
  # Defines an ingress rule that can be applied to an instance security group
  # Params:
  # +cidr_ip+:: an IPv4 CIDR range
  # +ip_protocol+:: IP protocol name or number
  # +from_port+:: start of port range for the +ip_protocol+
  # +to_port+:: end of port range for the +ip_protocol+
  
  attr_accessor :cidr_ip, :ip_protocol, :from_port, :to_port

  def initialize(
    cidr_ip = '0.0.0.0/0',
    ip_protocol = 'tcp',
    from_port = 22,
    to_port = 22
    )
      @cidr_ip = cidr_ip
      @ip_protocol = ip_protocol
      @from_port = from_port
      @to_port = to_port
  end

  def jsonify
    result = {
      'CidrIp' => @cidr_ip,
      'FromPort' => @from_port,
      'IpProtocol' => @ip_protocol,
      'ToPort' => @to_port
      }
    end
end

def main
  # Define default options
  options = {
    :instances => INSTANCES,
    :instance_type => INSTANCE_TYPE,
    :allow_ssh_from => ALLOW_SSH_FROM
    }

  # Parse user-defined options
  parser = OptionParser.new do |opt|
    opt.on('-i', '--instances NUM', Integer, 'Number of instances') do |o|
      options[:instances] = o
    end
    opt.on('-t', '--instance-type STR', String, 'Type of instance') do |o|
      options[:instance_type] = o
    end
    opt.on('-a', '--allow-ssh-from STR', String, 'Allow SSH from this IP') do |o|
      options[:allow_ssh_from] = o
    end
  end
  parser.parse!

  # Create objects using the user-defined options
  public_ip = PublicIP.new
  ingress_rule = create_ingress_rule(options[:allow_ssh_from])
  security_group = create_security_group(ingress_rule)
  instances = []

  (1..options[:instances]).each do |x|
    instances << create_instance(options[:instance_type], security_group)
  end

  # Create output string and use it to generate the JSON file
  output = format_output(public_ip, instances, security_group)
  File.open('output.json', 'w+') do |f|
    f.write(JSON.pretty_generate(output))
  end
end

if $PROGRAM_NAME == __FILE__
  main
end

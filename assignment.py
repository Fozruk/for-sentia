import argparse
import json

AWS_TEMPLATE_FORMAT_VERSION = '2010-09-09'
IMAGE_ID = 'ami-b97a12ce'

def outputsBlock(public_ip):
	return {'PublicIP' : public_ip.jsonify()}
	
def resourcesBlock(instances, security_group):
	result = {}
	for x in instances:
		result[x.name] = x.jsonify()
	result['InstanceSecurityGroup'] = security_group.jsonify()
	return result

def formatOutput(public_ip, instances, security_group):
	result = {}
	result['AWSTemplateFormatVersion'] = AWS_TEMPLATE_FORMAT_VERSION
	result['Outputs'] = outputsBlock(public_ip)
	result['Resources'] = resourcesBlock(instances, security_group)
	return result
	
class Options:
	instances = 1
	instance_type = 't2.micro'
	allow_ssh_from = ''


class PublicIP(object):
	description = "Public IP address of the newly created EC2 instance"
	
	def __init__(self):
		self._value = {'Fn::GetAtt' : ['EC2Instance', 'PublicIp']}

	@property
	def value(self):
		return self._value
		
	def jsonify(self):
		return {'Description' : PublicIP.description, 'Value' : self.value}

		
class EC2Instance(object):
	num = 0
	type = 'AWS::EC2::Instance'

	def __init__(self, image_id, instance_type, *security_groups):
		EC2Instance.num += 1
		self._name = self.getName()
		self._image_id = image_id
		self._instance_type = instance_type
		self._security_groups = security_groups
		
	@property
	def name(self):
		return self._name
		
	@property
	def image_id(self):
		return self._image_id
		
	@image_id.setter
	def image_id(self, value):
		self._image_id = value
		
	@property
	def instance_type(self):
		return self._instance_type
		
	@instance_type.setter
	def instance_type(self, value):
		self._instance_type = value
		
	@property
	def security_groups(self):
		return self._security_groups
		
	def getName(self):
		default = 'EC2Instance'
		if EC2Instance.num > 1:
			return "%s%d" % (default, EC2Instance.num)
		return default
		
	def jsonify(self):
		security_groups = []
		for x in self.security_groups:
			security_groups.append({'Ref' : 'InstanceSecurityGroup'})
		properties = {
			'ImageId' : self.image_id,
			'InstanceType' : self.instance_type,
			'SecurityGroups' : security_groups
			}
		return {'Properties' : properties, 'Type' : EC2Instance.type}
		

class SecurityGroup(object):
	type = 'AWS::EC2::SecurityGroup'

	def __init__(self, description = '', *rules):
		self._description = description
		self._security_group_ingress = rules
		
	@property
	def description(self):
		return self._description
		
	@description.setter
	def description(self, value):
		self._description = value
		
	@property
	def security_group_ingress(self):
		return self._security_group_ingress
	
	def addIngressRule(self, rule):
		self._security_group_ingress.append(rule)
		
	def jsonify(self):
		rules = [x.jsonify() for x in self.security_group_ingress]
		properties = {
			'GroupDescription' : self.description,
			'SecurityGroupIngress' : rules
			}
		return {'Properties' : properties, 'Type' : SecurityGroup.type}
	

class IngressRule(object):

	def __init__(
		self,
		cidr_ip = "0.0.0.0/0",
		ip_protocol = 'tcp',
		from_port = 22,
		to_port = 22):
			self._cidr_ip = self._setCidrIp(cidr_ip)
			self._ip_protocol = ip_protocol
			self._from_port = from_port
			self._to_port = to_port
	
	def _setCidrIp(self, ip):
		default = "0.0.0.0/0"
		if ip == '':
			return default
		elif ip != default:
			return "%s%s" % (ip, "/32")
		return default
	  
	@property
	def cidr_ip(self):
		return self._cidr_ip

	@cidr_ip.setter
	def cidr_ip(self, value):
		self._cidr_ip = value
	
	@property
	def ip_protocol(self):
		return self._ip_protocol
	
	@ip_protocol.setter
	def ip_protocol(self, value):
		self._ip_protocol = value
	
	@property
	def from_port(self):
		return self._from_port
	
	@from_port.setter
	def from_port(self, value):
		self._from_port = value
	
	@property
	def to_port(self):
		return self._to_port
	
	@to_port.setter
	def to_port(self, value):
		self._to_port = value
	
	def jsonify(self):
		return {
			'CidrIp' : self.cidr_ip,
			'FromPort' : str(self.from_port),
			'IpProtocol' : self.ip_protocol,
			'ToPort' : str(self.to_port)
			}

def main():
	# Create parser, add options, and parse args.
	parser = argparse.ArgumentParser(description = "Parse some stuff.")
	parser.add_argument(
		'-i',
		'--instances',
		dest = 'instances',
		default = 1, type = int
		)
	parser.add_argument(
		'-t',
		'--instance-type',
		dest = 'instance_type',
		default = 't2.micro',
		type = str
		)
	parser.add_argument(
		'-a',
		'--allow-ssh-from',
		dest = 'allow_ssh_from',
		default = '',
		type = str
		)
	opts = Options()
	parser.parse_args(namespace = opts)
				
	# Create objects using user-defined options.
	public_ip = PublicIP()
	rule = IngressRule(cidr_ip = opts.allow_ssh_from)
	security_group = SecurityGroup('Enable SSH access via port 22', rule)
	instances = [EC2Instance(IMAGE_ID, opts.instance_type, security_group) \
			for x in range(0, opts.instances)]
			
	# Create output string and use it to generate the JSON file.
	output = formatOutput(public_ip, instances, security_group)
	with open("temp.json", "w+") as f:
		f.write(json.dumps(output, sort_keys=True, indent=2))

if __name__ == '__main__':
	main()
